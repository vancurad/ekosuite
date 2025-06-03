from abc import ABC, abstractmethod
from datetime import datetime
from haversine import haversine, Unit
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
from .ImageData import ImageData

class Image(ABC):
    """
    Abstract base class for image processing.
    """

    @property
    def image_data(self) -> ImageData:
        """
        Returns the image data.
        """
        pass

    @property
    def filename(self) -> str:
        """
        Returns the filename of the image.
        """
        pass

    @property
    def create_time(self) -> datetime:
        """
        Returns the creation time of the image.
        """
        pass
    
    @property
    def latitude(self) -> float:
        """
        Returns the latitude of the location where the image was taken
        """
        pass
    
    @property
    def longitude(self) -> float:
        """
        Returns the longitude of the location where the image was taken
        """
        pass
    
    @property
    def timezone_offset(self) -> float | None:
        """
        Returns the timezone offset for where the image was taken or None if timezone is unknown
        """
        if self.latitude is not None and self.longitude is not None:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=float(self.latitude), lng=float(self.longitude))
            local_tz = timezone(timezone_str)
            utc_offset = local_tz.utcoffset(datetime.now())
            return utc_offset.total_seconds() / 3600
        else:
            return None

    @property
    def image_width(self) -> int:
        """
        Returns the width of the image.
        """
        pass

    @property
    def image_height(self) -> int:
        """
        Returns the height of the image.
        """
        pass

    @property
    def pixel_size(self) -> float:
        """
        Returns the pixel size of the image.
        """
        pass

    @property
    def object(self) -> str:
        """
        Returns the object associated with the image.
        """
        pass

    @property
    def ra(self) -> float:
        """
        Returns the right ascension of the image.
        """
        pass

    @property
    def dec(self) -> float:
        """
        Returns the declination of the image.
        """
        pass

    @property
    def instrument(self) -> str:
        """
        Returns the camera used for acquisition.
        """
        pass

    @property
    def telescope(self) -> str:
        """
        Returns the telescope used for acquisition.
        """
        pass

    @property
    def filter(self) -> str:
        """
        Returns the filter used for the image.
        """
        pass

    @property
    def imagetype(self) -> str:
        """
        Returns the type of the image.
        """
        pass

    @property
    def exptime(self) -> float:
        """
        Returns the exposure time of the image.
        """
        pass

    @property
    def focal_length(self) -> float:
        """
        Returns the focal length used for the image.
        """
        pass

    @property
    def temperature(self) -> float:
        """
        Returns the temperature during the image capture.
        """
        pass

    @property
    def sensor_temperature(self) -> float:
        """
        Returns the sensor temperature during the image capture.
        """
        pass

    @property
    def gain(self) -> float:
        """
        Returns the gain of the image.
        """
        pass

    @property
    def bias(self) -> float:
        """
        Returns the bias of the image.
        """
        pass

    @property
    def airmass(self) -> float:
        """
        Returns the airmass of the image.
        """
        pass

    @property
    def mpsas(self) -> float:
        """
        Returns the MPSAS of the image.
        """
        pass

    @property
    def scale(self) -> float:
        """
        Returns the scale of the image in arc seconds per pixel.
        """
        pass

    def angular_separation(self, ra: float, dec: float) -> float:
        """
        Returns the angular separation between the image and a given RA and DEC.
        """
        return haversine(
            (self.dec, self.ra),
            (dec, ra),
            unit=Unit.DEGREES,
            normalize=True,
            check=False,
        )