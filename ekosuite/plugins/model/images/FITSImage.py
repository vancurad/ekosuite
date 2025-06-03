import fitsio
from fitsio import FITS, FITSHDR
from .Image import Image
from .ImageData import ImageData
from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
import time

class FITSImage(Image):

    """
    A class to handle FITS image files.
    """
    def __init__(self, source: str):
        self._source = source
    
    def __del__(self):
        if hasattr(self, '_fits'):
            self._fits.close()
    
    def _header(self) -> FITSHDR:
        if not hasattr(self, '_hdr'):
            try:
                self._hdr = fitsio.read_header(self._source, ext=0)
            except OSError as e:
                # in case of a read error, retry after a short delay
                # this is useful for files that are still being written
                print(f"Error reading FITS header: {e}.")
                raise e
        return self._hdr

    @property
    def image_data(self) -> ImageData:
        image_data = fitsio.read(self._source)
        return ImageData(image_data)

    @property
    def fits(self) -> FITS:
        if not hasattr(self, '_fits'):
            self._fits = self._fetchFITS()
        return self._fits

    def _fetchFITS(self) -> FITS:
        return FITS(self._source)
    
    @property
    def mpsas(self) -> float:
        mpsas_value = self._header().get('MPSAS', -1)
        return mpsas_value if not None else -1
    
    @property
    def filename(self) -> str:
        return self._source

    @property
    def create_time(self) -> datetime:
        date_obs = self._header().get('DATE-OBS', None) # UTC time
        return datetime.strptime(date_obs, '%Y-%m-%dT%H:%M:%S.%f')
    
    @property
    def latitude(self) -> float:
        return self._header().get('SITELAT', None)
    
    @property
    def longitude(self) -> float:
        return self._header().get('SITELONG', None)

    @property
    def filename(self) -> str:
        return self._source

    @property
    def image_width(self) -> int:
        return self._header().get('NAXIS1', -1)

    @property
    def image_height(self) -> int:
        return self._header().get('NAXIS2', -1)

    @property
    def pixel_size(self) -> float:
        return self._header().get('XPIXSZ', -1)

    @property
    def object(self) -> str:
        return self._header().get('OBJECT', 'Unknown')

    @property
    def ra(self) -> float:
        return self._header().get('RA', -1)

    @property
    def dec(self) -> float:
        return self._header().get('DEC', -1)
    
    @property
    def instrument(self) -> str:
        return self._header().get('INSTRUME', 'Unknown')

    @property
    def telescope(self) -> str:
        return self._header().get('TELESCOP', 'Unknown')

    @property
    def filter(self) -> str | None:
        return self._header().get('FILTER', None)

    @property
    def imagetype(self) -> str:
        return self._header().get('IMAGETYP', 'Unknown')

    @property
    def exptime(self) -> float:
        return self._header().get('EXPTIME', -1)

    @property
    def focal_length(self) -> float | None:
        return self._header().get('FOCALLEN', None)

    @property
    def temperature(self) -> float | None:
        return self._header().get('FOCUSTEM', None)

    @property
    def sensor_temperature(self) -> float | None:
        return self._header().get('CCD-TEMP', None)

    @property
    def gain(self) -> float | None:
        return self._header().get('GAIN', None)

    @property
    def bias(self) -> float | None:
        return self._header().get('OFFSET', None)

    @property
    def airmass(self) -> float | None:
        return self._header().get('AIRMASS', None)

    @property
    def mpsas(self) -> float | None:
        return self._header().get('MPSAS', None)