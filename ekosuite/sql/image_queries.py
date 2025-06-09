from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.model.images.DBImage import DBImage

def night_session_for_image(db: AppDB, image_id: int) -> int | None:
    """
    Get the night session ID for a given image ID.
    :param image_id: The ID of the image.
    :return: The night session ID.
    """
    result = next(iter(db.fetchall("""
        SELECT night_session_id FROM night_session_fits_files
        WHERE fits_file_id = ?
        LIMIT 1
    """, (image_id,))), None)
    return result[0] if result is not None else None

def flat_frames_for_image(db: AppDB, image_id: int) -> list[int] | None:
    """
    Get the flat frames for a given image ID.
    :param image_id: The ID of the image.
    :return: A list of flat frame IDs.
    """
    night_session_id = night_session_for_image(db, image_id)
    image = DBImage(image_id, db)
    return list(value[0] for value in db.fetchall("""
            SELECT ff.id FROM fits_files ff
            JOIN night_session_fits_files nsff
                ON nsff.fits_file_id = ff.id
            WHERE nsff.night_session_id = ?
            AND ff.image_type_generic = 'FLAT'
            AND ff.filter = ?
            AND ff.telescope = ?
            AND ff.instrument = ?
            ORDER BY ABS(TIMEDIFF(ff.create_time, ?)) ASC
    """, (night_session_id, image.filter, image.telescope, image.instrument, image.create_time)))

def master_bias_for_image(db: AppDB, image_id: int) -> int | None:
    image = DBImage(image_id, db)
    result = next(iter(db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER BIAS'
            AND instrument = ?
            AND gain = ?
            AND bias = ?
            AND sensor_temperature = ?
            ORDER BY ABS(TIMEDIFF(create_time, ?)) ASC
            LIMIT 1
    """, (image.instrument, image.gain, image.bias, image.sensor_temperature, image.create_time,))), None)
    return result[0] if result is not None else None

def master_dark_for_image(db: AppDB, image_id: int) -> int | None:
    image = DBImage(image_id, db)
    result = next(iter(db.fetchall("""
            SELECT id FROM fits_files
            WHERE image_type_generic = 'MASTER DARK'
            AND instrument = ?
            AND gain = ?
            AND exptime = ?
            AND bias = ?
            AND sensor_temperature = ?
            ORDER BY ABS(TIMEDIFF(create_time, ?)) ASC
            LIMIT 1
    """, (image.instrument, image.gain, image.exptime, image.bias, image.sensor_temperature, image.create_time,))), None)
    return result[0] if result is not None else None