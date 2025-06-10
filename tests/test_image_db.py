from tests import testdata
from ekosuite import FileSystemImageChangeListener
import os
import pytest
import time
import asyncio
from datetime import datetime

@pytest.fixture(autouse=True)
def setup_before_each_test():
    testdata.cleanup()
    yield
    # _cleanup()

def test_import_images_across_nights_a():
    """
    Test the import of images across different nights.
    """

    # Timezone in test data is UTC-7. 
    # Local time here is an image 1 minute past noon on 1st (count into the 1st)
    # and an image 1 second before noon on 2nd (still count into the 1st)
    testdata.create_test_fits(filename='test_image_1.fits', date=datetime(2023, 10, 1, 19, 0, 1))
    testdata.create_test_fits(filename='test_image_2.fits', date=datetime(2023, 10, 2, 18, 59, 59))
    
    # Prepare the environment
    environment = testdata.environment()

    testdata.wait_after_saving_images(environment, 2)

    fetched_images = environment['db'].execute("SELECT COUNT(*) FROM fits_files").fetchone()
    fetched_night_sessions = environment['db'].execute("SELECT COUNT(*) FROM night_sessions").fetchone()

    assert fetched_images[0] == 2, "Failed to import images across nights"
    assert fetched_night_sessions[0] == 1, "Expected 1 night session for both images"

def test_import_images_across_nights_b():
    """
    Test the import of images across different nights.
    """

    # Timezone in test data is UTC-7. 
    # Local time here is an image 1 minute past noon on 1st (count into the 1st)
    # and an image 1 second after noon on 2nd (no longer count into the 1st)
    testdata.create_test_fits(filename='test_image_1.fits', date=datetime(2023, 10, 1, 19, 0, 1))
    testdata.create_test_fits(filename='test_image_2.fits', date=datetime(2023, 10, 2, 19, 0, 1))
    
    # Prepare the environment
    environment = testdata.environment()

    testdata.wait_after_saving_images(environment, 2)

    fetched_images = environment['db'].execute("SELECT COUNT(*) FROM fits_files").fetchone()
    fetched_night_sessions = environment['db'].execute("SELECT COUNT(*) FROM night_sessions").fetchone()

    assert fetched_images[0] == 2, "Failed to import images across nights"
    assert fetched_night_sessions[0] == 2, "Expected 1 night session for each image"
