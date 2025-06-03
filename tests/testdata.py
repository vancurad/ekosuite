import asyncio
import os
import time
import numpy as np
from datetime import datetime
from astropy.nddata import CCDData
from astropy.io import fits

from ekosuite import AppDB, FileSystemObserver, FileSystemImageChangeListener
from ekosuite import ProjectDB

def test_data_folder():
    return os.path.join(os.path.dirname(__file__), "__data__")

def create_test_fits(filename='test_image.fits', 
                     shape=(100, 100), 
                     date=datetime.now(), 
                     sitelat=34.0, 
                     sitelong=-118.0, 
                     object='Test Object', 
                     mpsas=20.0, 
                     telescope='Test Telescope', 
                     instrument='Test Instrument', 
                     bunit='adu', 
                     ra=0.0, 
                     dec=0.0,
                     image_type='light'):
    """
    Create a FITS file with random test data in the specified folder.
    """
    test_folder = test_data_folder()
    # Ensure the folder exists
    os.makedirs(test_folder, exist_ok=True)
    filepath = os.path.join(test_folder, filename)

    # Generate test data (e.g., a 100x100 array of random floats)
    data = np.random.rand(*shape)

    # Create a Primary HDU object
    hdu = fits.PrimaryHDU(data)
    # hdu.header['SIMPLE'] = 'T'
    hdu.header['BZERO'] = 32768
    hdu.header['BSCALE'] = 1
    hdu.header['BITPIX'] = 16
    hdu.header['DATE-OBS'] = date.strftime('%Y-%m-%dT%H:%M:%S.%f')
    hdu.header['SITELAT'] = sitelat
    hdu.header['SITELONG'] = sitelong
    hdu.header['NAXIS1'] = shape[0]
    hdu.header['NAXIS2'] = shape[1]
    hdu.header['XPIXSZ'] = 0.5
    hdu.header['OBJECT'] = object
    hdu.header['MPSAS'] = mpsas
    hdu.header['BUNIT'] = bunit
    hdu.header['TELESCOP'] = telescope
    hdu.header['INSTRUME'] = instrument
    hdu.header['RA'] = ra
    hdu.header['DEC'] = dec
    hdu.header['IMAGETYP'] = image_type

    hdul = fits.HDUList([hdu])

    # Write the FITS file
    hdul.writeto(filepath, overwrite=True)
    return filepath

def environment(fileChangeListeners: set[FileSystemImageChangeListener] = set()):
    db = AppDB(folder=test_data_folder())
    projectDB = ProjectDB(db)
    projectDB.selectedFolders = [test_data_folder()]
    fileSystemObserver = FileSystemObserver(db, listeners=fileChangeListeners)
    return {
        "db": db,
        "projectDB": projectDB,
        "fileSystemObserver": fileSystemObserver,
    }

def wait_after_saving_images(environment, nimages: int):
    image_count = 0

    def insertImage(image):
        nonlocal image_count
        asyncio.run(environment['projectDB'].insertImage(image))
        image_count += 1

    environment['fileSystemObserver'].addListener(FileSystemImageChangeListener(lambda image: insertImage(image)))

    # Await SQL inserts
    ct = 0
    while image_count < nimages:
        time.sleep(0.1)
        ct += 1
        if ct > 30:
            break
    time.sleep(0.5)