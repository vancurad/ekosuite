from xisf import XISF

from .Image import Image
from .ImageData import ImageData
from datetime import datetime

class XISFImage(Image):

    """
    A class to handle FITS image files.
    """
    def __init__(self, source: str):
        self._source = source
        self._header = XISF(self._source).get_images_metadata()[0]['FITSKeywords']
    
    def _fetchValue(self, key: str, default: any = None) -> any:
        values = self._header.get(key)
        if values is None:
            return default
        return values[0]['value']
    
    @property
    def image_data(self) -> ImageData:
        image_data = XISF(self._source).read_image(0)
        return ImageData(image_data)
    
    @property
    def mpsas(self) -> float:
        mpsas_value = self._fetchValue('MPSAS', -1)
        return mpsas_value if not None else -1
    
    @property
    def filename(self) -> str:
        return self._source

    @property
    def create_time(self) -> datetime:
        date_obs = self._fetchValue('DATE-OBS', None) # UTC time
        return datetime.strptime(date_obs, '%Y-%m-%dT%H:%M:%S.%f')
    
    @property
    def latitude(self) -> float:
        return self._fetchValue('SITELAT', None)
    
    @property
    def longitude(self) -> float:
        return self._fetchValue('SITELONG', None)

    @property
    def filename(self) -> str:
        return self._source

    @property
    def image_width(self) -> int:
        return self._fetchValue('NAXIS1', -1)

    @property
    def image_height(self) -> int:
        return self._fetchValue('NAXIS2', -1)

    @property
    def pixel_size(self) -> float:
        return self._fetchValue('XPIXSZ', -1)

    @property
    def object(self) -> str:
        return self._fetchValue('OBJECT', 'Unknown')

    @property
    def ra(self) -> float:
        return self._fetchValue('RA', -1)

    @property
    def dec(self) -> float:
        return self._fetchValue('DEC', -1)
    
    @property
    def instrument(self) -> str:
        return self._fetchValue('INSTRUME', 'Unknown')

    @property
    def telescope(self) -> str:
        return self._fetchValue('TELESCOP', 'Unknown')

    @property
    def filter(self) -> str | None:
        return self._fetchValue('FILTER', None)

    @property
    def imagetype(self) -> str:
        return self._fetchValue('IMAGETYP', 'Unknown')

    @property
    def exptime(self) -> float:
        return self._fetchValue('EXPTIME', -1)

    @property
    def focal_length(self) -> float | None:
        return self._fetchValue('FOCALLEN', None)

    @property
    def temperature(self) -> float | None:
        return self._fetchValue('FOCUSTEM', None)

    @property
    def sensor_temperature(self) -> float | None:
        return self._fetchValue('CCD-TEMP', None)

    @property
    def gain(self) -> float | None:
        return self._fetchValue('GAIN', None)

    @property
    def bias(self) -> float | None:
        return self._fetchValue('OFFSET', None)

    @property
    def airmass(self) -> float | None:
        return self._fetchValue('AIRMASS', None)

    @property
    def mpsas(self) -> float | None:
        return self._fetchValue('MPSAS', None)