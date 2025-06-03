from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.models.images.ImageData import ImageData
from ekosuite.plugins.models.images.Image import Image
from ekosuite.plugins.models.images.DBImage import DBImage
import ekosuite.sql.image_queries as sql
import asyncio

class AnalysisResult:
    def __init__(self, db: AppDB, id: int):
        self._db = db
        self._id = id

    @property
    def fwhm(self) -> float:
        """
        Full Width at Half Maximum (FWHM) of the image.
        :return: FWHM value.
        """
        return self._db.fetchall("SELECT fwhm FROM image_analysis WHERE id = ?", (self._id,))[0]
    
    @property
    def snr(self) -> float:
        """
        Signal-to-Noise Ratio (SNR) of the image.
        :return: SNR value.
        """
        return self._db.fetchall("SELECT snr FROM image_analysis WHERE id = ?", (self._id,))[0]
    
    @property
    def eccentricity(self) -> float:
        """
        Eccentricity of stars in the image.
        :return: Eccentricity value.
        """
        return self._db.fetchall("SELECT eccentricity FROM image_analysis WHERE id = ?", (self._id,))[0]
    
    @property
    def median(self) -> float:
        """
        Median value of the image.
        :return: Median value.
        """
        return self._db.fetchall("SELECT median FROM image_analysis WHERE id = ?", (self._id,))[0]

class ImageAnalysisCache:
    def __init__(self, db: AppDB):
        self._db = db
        self._master_flats = {}
        self._processed_flats = []
    
    def master_flat(self, image: Image) -> ImageData | None:
        """
        Get the master flat for the image.
        :param image: The image to get the master flat for.
        :return: The master flat image.
        """
        night_session_id = self._db.fetchall("""
            SELECT night_session_id FROM night_session_fits_files
            WHERE fits_file_id = ?
            LIMIT 1
        """, (image.id,))[0]
        
        return self._master_flats[night_session_id]

    async def make(self, image: Image):
        """
        Get the master flat for the image.
        :param image: The image to get the master flat for.
        :return: The master flat image.
        """
        night_session_id = sql.night_session_for_image(self._db, image.id)

        if night_session_id not in self._processed_flats:
            self._processed_flats.append(night_session_id)
        else:
            return

        flat_frame_ids = sql.flat_frames_for_image(self._db, image.id)

        master_bias_id = self._db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER BIAS'
            ORDER BY ABS(TIMEDIFF(created_date, ?)) ASC
            LIMIT 1
        """, (image.created_date,))[0]

        self._master_flats[night_session_id] = ImageData.flat_stack(
            (DBImage(self._db, flat_id).image_data for flat_id in (flat_frame_ids if flat_frame_ids else [])), 
            DBImage(self._db, master_bias_id).image_data
        )
    
class ImageAnalysis:
    def __init__(self, db: AppDB, images: list[Image]):
        self._images = images
        self._db = db
        self._cache = ImageAnalysisCache(db)

    async def analyze(self, calibrate: bool):
        """
        Analyze the image and return the analysis result.
        :param calibrate: If True, perform calibration on the image.
        :return: Analysis result.
        """
        analyzed_images = []
        if calibrate:
            for image in self._images:
                asyncio.create_task(self._cache.make(image))
            
            for image in self._images:
                flat = self._cache.master_flat(image)
                    
                dark = sql.master_dark_for_image(self._db, image.id)
                bias = sql.master_bias_for_image(self._db, image.id)
                if flat is None:
                    raise ValueError("No flats found for the image.")
                if dark is None:
                    raise ValueError("No darks found for the image.")
                if bias is None:
                    raise ValueError("No biases found for the image.")
                analyzed_images.append(self.calibrate(image, flat, dark, bias))
        else:
            for image in self._images:
                analyzed_images.append(image.image_data._ccdData)
        # Perform analysis on the image
        results = (self.analyze_calibrated(image) for image in analyzed_images)
        return results

    def analyze_calibrated(self, image: Image) -> AnalysisResult:
        pass

    def calibrate(self, light: Image, flat: Image, master_dark: Image, master_bias: Image):
        """
        Calibrate the image.
        :return: None
        """
        calibrated_image = light.image_data.calibrate(
            DBImage(self._db, master_bias).image_data,
            DBImage(self._db, master_dark).image_data,
            DBImage(self._db, flat).image_data
        )
        return calibrated_image