from numpy import ndarray
from numpy import float64
from numpy import squeeze

from astropy import nddata, units
from astropy.nddata import CCDData
import ccdproc as ccdp

class ImageData:
    def __init__(self, raw_data: ndarray):
        self._raw_data = raw_data
    
    def bias_subtract(self, bias: "ImageData") -> CCDData:
        """
        Subtracts the bias from the raw data.
        """
        bias_ccdData = bias.ccdData
        if bias_ccdData.shape[-1] == 1 and self.ccdData.shape[-1] != 1:
            bias_ccdData = CCDData(squeeze(bias_ccdData, axis=-1), unit=bias.ccdData.unit)
        return ccdp.subtract_bias(self.ccdData, bias_ccdData)
    
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
    
    def calibrate(self, bias: "ImageData", dark: "ImageData", flat: "ImageData", exposure_time: float) -> CCDData:
        """
        Calibrates the raw data by subtracting the bias and dark, and dividing by the flat.
        """
        master_dark = dark.bias_subtract(bias)
        if master_dark.shape[-1] == 1 and self.ccdData.shape[-1] != 1:
            master_dark = CCDData(squeeze(master_dark, axis=-1), unit=bias.ccdData.unit)
        ccdData = self.ccdData
        ccdData.meta['exposure_time'] = exposure_time
        master_dark.meta['exposure_time'] = exposure_time
        dark_corrected = ccdp.subtract_dark(ccdData, master_dark, exposure_time='exposure_time', exposure_unit=units.second)
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