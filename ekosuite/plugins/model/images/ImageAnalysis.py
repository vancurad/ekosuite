from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.model.images.ImageData import ImageData
from ekosuite.plugins.model.images.Image import Image
from ekosuite.plugins.model.images.DBImage import DBImage
import ekosuite.sql.image_queries as sql
import asyncio
from photutils.detection import DAOStarFinder
from photutils.psf import fit_fwhm
from astropy.nddata import CCDData

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
        result = next(iter(self._db.fetchall("SELECT fwhm FROM image_analysis WHERE id = ?", (self._id,))))
        return result[0] if result else 0.0
    
    @property
    def snr(self) -> float:
        """
        Signal-to-Noise Ratio (SNR) of the image.
        :return: SNR value.
        """
        result = next(iter(self._db.fetchall("SELECT snr FROM image_analysis WHERE id = ?", (self._id,))))
        return result[0] if result else 0.0
    
    @property
    def eccentricity(self) -> float:
        """
        Eccentricity of stars in the image.
        :return: Eccentricity value.
        """
        result = self._db.fetchall("SELECT eccentricity FROM image_analysis WHERE id = ?", (self._id,))
        return result[0] if result else 0.0
    
    @property
    def median(self) -> float:
        """
        Median value of the image.
        :return: Median value.
        """
        result = next(iter(self._db.fetchall("SELECT median FROM image_analysis WHERE id = ?", (self._id,))))
        return result[0] if result else 0.0

class ImageAnalysisCache:
    def __init__(self, db: AppDB):
        self._db = db
        self._master_flats = {}
        self._processed_flats = []
    
    def master_flat(self, image: DBImage) -> ImageData | None:
        """
        Get the master flat for the image.
        :param image: The image to get the master flat for.
        :return: The master flat image.
        """
        night_session_id = next(iter(self._db.fetchall("""
            SELECT night_session_id FROM night_session_fits_files
            WHERE fits_file_id = ?
            LIMIT 1
        """, (image._id,))), None)

        if night_session_id is None:
            return None
        
        return self._master_flats.get(night_session_id[0])

    async def make(self, image: DBImage):
        """
        Get the master flat for the image.
        :param image: The image to get the master flat for.
        :return: The master flat image.
        """
        night_session_id = sql.night_session_for_image(self._db, image._id)

        if night_session_id not in self._processed_flats:
            self._processed_flats.append(night_session_id)
        else:
            return

        flat_frame_ids = sql.flat_frames_for_image(self._db, image._id)

        master_bias_id = self._db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER BIAS'
            ORDER BY ABS(TIMEDIFF(create_time, ?)) ASC
            LIMIT 1
        """, (image.create_time,))

        if len(master_bias_id) == 0:
            return
        master_bias_id = master_bias_id[0][0]

        self._master_flats[night_session_id] = ImageData.flat_stack(
            list(DBImage(flat_id, self._db).image_data for flat_id in (flat_frame_ids if flat_frame_ids else [])), 
            DBImage(master_bias_id, self._db).image_data
        )
    
class ImageAnalysis:
    def __init__(self, db: AppDB, images: list[DBImage]):
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
                await asyncio.create_task(self._cache.make(image))
            
            for image in self._images:
                flat = self._cache.master_flat(image)
                    
                dark = sql.master_dark_for_image(self._db, image._id)
                bias = sql.master_bias_for_image(self._db, image._id)
                if flat is None:
                    raise ValueError("No flats found for the image.")
                if dark is None:
                    raise ValueError("No darks found for the image.")
                if bias is None:
                    raise ValueError("No biases found for the image.")
                analyzed_images.append(self.calibrate(
                    image.image_data, 
                    flat, 
                    DBImage(dark, self._db).image_data, 
                    DBImage(bias, self._db).image_data,
                    image.exptime if image.exptime else 1.0
                ))
        else:
            for image in self._images:
                analyzed_images.append(image.image_data.ccdData)
        # Perform analysis on the image
        results = list(self.analyze_calibrated(image, dbimage._id) for (image, dbimage) in zip(analyzed_images, self._images))
        return results

    def analyze_calibrated(self, image: CCDData, image_id: int) -> AnalysisResult:
        print("Analyzing image...")
        star_finder = DAOStarFinder(threshold=5.0, fwhm=3.0)
        stars = star_finder(image.data)
        print("Got stars:", stars)

        if stars is None or len(stars) == 0:
            raise ValueError("No stars found in the image for analysis.")
        stars = stars[0:min(30, len(stars))]  # Limit to first 10 stars for analysis
        fwhm = fit_fwhm(image.data, xypos=[(x, y) for x, y in zip(stars['xcentroid'], stars['ycentroid'])], fit_shape=(7, 7))
        fwhm = next(iter(fwhm))
        self._db.execute("""
            INSERT OR REPLACE INTO image_analysis (image_id, fwhm, snr, eccentricity, median)
            VALUES (?, ?, ?, ?, ?)
        """, (image_id, fwhm, 0, 0, 0))
        analysis_id = self._db.execute("SELECT id FROM image_analysis WHERE image_id = ?", (image_id, )).fetchone()
        analysis_id = analysis_id[0] if analysis_id else None
        if analysis_id is None:
            raise ValueError("Failed to insert analysis result into the database.")
        result = AnalysisResult(self._db, analysis_id)
        return result

    def calibrate(self, light: ImageData, flat: ImageData, master_dark: ImageData, master_bias: ImageData, exposure_time: float):
        """
        Calibrate the image.
        :return: None
        """
        calibrated_image = light.calibrate(
            master_bias,
            master_dark,
            flat,
            exposure_time
        )
        return calibrated_image