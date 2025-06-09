from tests import testdata
import os
import pytest
import shutil
from ekosuite.plugins.model.images.DBImage import DBImage
from ekosuite.plugins.model.images.ImageAnalysis import ImageAnalysis, AnalysisResult

@pytest.fixture(autouse=True)
def setup_before_each_test():
    testdata.cleanup()

@pytest.mark.asyncio
async def test_setup_library():
    """
    Test the setup of the library.
    """
    # Ensure the test data folder exists
    test_data_folder = testdata.test_data_folder()
    os.makedirs(test_data_folder, exist_ok=True)

    # Prepare the environment
    environment = testdata.environment()

    testdata.wait_after_saving_images(environment, 8, lambda: shutil.copytree('tests/samples', os.path.join(test_data_folder, 'samples'), dirs_exist_ok=True))
    
    # Check if the folder is created
    assert os.path.exists(test_data_folder), "Test data folder was not created."

    light_frame_data = environment['db'].execute("""
        SELECT id FROM fits_files WHERE image_type_generic = 'LIGHT'
    """).fetchall()

    images = [DBImage(id=light_frame_id[0], db=environment['db']) for light_frame_id in light_frame_data]

    image_analysis = ImageAnalysis(images=images, db=environment['db'])
    results = await image_analysis.analyze(calibrate=True)

    assert len(results) == len(images), "Image analysis did not return the expected number of results."

    if len(results) > 2:
        assert abs(results[0].fwhm - 148) < 1, "FWHM value for the first image is not as expected."
        assert abs(results[1].fwhm - 137) < 1, "FWHM value for the second image is not as expected."
        assert abs(results[2].fwhm - 126) < 1, "FWHM value for the third image is not as expected."