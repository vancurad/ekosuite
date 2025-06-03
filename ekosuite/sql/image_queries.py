from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.models.images.DBImage import DBImage

def night_session_for_image(db: AppDB, image_id: int) -> int:
    """
    Get the night session ID for a given image ID.
    :param image_id: The ID of the image.
    :return: The night session ID.
    """
    return db.fetchall("""
        SELECT night_session_id FROM night_session_fits_files
        WHERE fits_file_id = ?
        LIMIT 1
    """, (image_id,))[0]

def flat_frames_for_image(db: AppDB, image_id: int) -> list[int] | None:
    """
    Get the flat frames for a given image ID.
    :param image_id: The ID of the image.
    :return: A list of flat frame IDs.
    """
    night_session_id = night_session_for_image(db, image_id)
    image = DBImage(image_id, db)
    return db.fetchall("""
            SELECT ff.id FROM fits_files ff
            JOIN night_session_fits_files nsff
                ON nsff.fits_file_id = ff.id
            WHERE nsff.night_session_id = ?
            AND ff.image_type_generic = 'FLAT'
            AND ff.filter = ?
            AND ff.telescope = ?
            AND ff.instrument = ?
            ORDER BY ABS(TIMEDIFF(ff.created_date, ?)) ASC
    """, (night_session_id, image.filter, image.telescope, image.instrument, image.created_date))

def master_bias_for_image(db: AppDB, image_id: int) -> int | None:
    image = DBImage(image_id, db)
    return next(iter(db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER BIAS'
            AND instrument = ?
            AND gain = ?
            AND bias = ?
            AND sensor_temperature = ?
            ORDER BY ABS(TIMEDIFF(created_date, ?)) ASC
            LIMIT 1
    """, (image.instrument, image.gain, image.bias, image.sensor_temperature, image.created_date,))))

def master_dark_for_image(db: AppDB, image_id: int) -> int | None:
    image = DBImage(image_id, db)
    return next(iter(db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER DARK'
            AND exposure_time = ?
            AND gain = ?
            AND bias = ?
            AND sensor_temperature = ?
            ORDER BY ABS(TIMEDIFF(created_date, ?)) ASC
            LIMIT 1
    """, (image.instrument, image.gain, image.exposure_time, image.sensor_temperature, image.created_date,))))