from numpy import ndarray
from numpy import float64

from astropy import nddata
from astropy.nddata import CCDData
import ccdproc as ccdp

class ImageData:
    def __init__(self, raw_data: ndarray):
        self._raw_data = raw_data
    
    def bias_subtract(self, bias: "ImageData") -> CCDData:
        """
        Subtracts the bias from the raw data.
        """
        return ccdp.subtract_bias(self.ccdData, bias.ccdData)
    
    def dark_subtract(self, dark: "ImageData") -> CCDData:
        """
        Subtracts the dark from the raw data.
        """
        return ccdp.subtract_dark(self.ccdData, dark.ccdData)
    
    @staticmethod
    def flat_stack(flats: list["ImageData"], bias: "ImageData") -> CCDData:
        """
        Stacks the flats.
        """
        flat_data = [flat.bias_subtract(bias) for flat in flats]
        return ccdp.combine(flat_data, sigma_clip=True)
    
    def calibrate(self, bias: "ImageData", dark: "ImageData", flat: "ImageData") -> CCDData:
        """
        Calibrates the raw data by subtracting the bias and dark, and dividing by the flat.
        """
        master_dark = dark.bias_subtract(bias)
        dark_corrected = ccdp.subtract_dark(self.ccdData, master_dark)
        return ccdp.flat_correct(dark_corrected, flat)
    
    def flat_correct(self, flat: "ImageData") -> CCDData:
        """
        Divides the raw data by the flat.
        """
        return ccdp.flat_correct(self.ccdData, flat.ccdData)
    
    @property
    def ccdData(self) -> CCDData:
        """
        Returns the raw data as a CCDData object.
        """
        return CCDData(self._raw_data, unit='adu')