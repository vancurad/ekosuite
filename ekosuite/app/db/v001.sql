PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS plugin_selection (
    name TEXT NOT NULL PRIMARY KEY,
    idx INTEGER UNIQUE
);

CREATE TABLE IF NOT EXISTS dbinfo (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    item TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS analyzed_files (
    filename TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fits_files (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    create_time TEXT NOT NULL,
    lat REAL,
    lon REAL,
    timezone_offset REAL,
    image_width INTEGER,
    image_height INTEGER,
    pixel_size REAL,
    scale REAL,
    object TEXT,
    ra REAL,
    dec REAL,
    instrument TEXT,
    telescope TEXT,
    filter TEXT,
    imagetype TEXT,
    exptime REAL,
    focal_length REAL,
    temperature REAL,
    sensor_temperature REAL,
    gain REAL,
    bias REAL,
    mpsas REAL,
    airmass REAL,
    image_type_generic TEXT GENERATED ALWAYS AS (
        CASE
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'light' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'lightframe'
                THEN 'LIGHT'
            WHEN
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'dark' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'darkframe'
                THEN 'DARK'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'flat' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'flatframe'
                THEN 'FLAT'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'bias' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'biasframe'
                THEN 'BIAS'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterbias' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterbiasframe'
                THEN 'MASTER BIAS'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterlight' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterlightframe'
                THEN 'MASTER LIGHT'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterdark' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterdarkframe'
                THEN 'MASTER DARK'
            WHEN 
                REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterflat' 
                OR REPLACE(LOWER(imagetype), ' ', '') LIKE 'masterflatframe'
                THEN 'MASTER FLAT'
            ELSE 'UNKNOWN'
        END
    ) STORED
);

CREATE TABLE IF NOT EXISTS image_analysis (
    id INTEGER PRIMARY KEY,
    image_id INTEGER NOT NULL,
    fwhm REAL,
    snr REAL,
    eccentricity REAL,
    median REAL,
    FOREIGN KEY (image_id) REFERENCES fits_files(id)
);

CREATE INDEX idx_fits_files_filter ON fits_files(filter);
CREATE INDEX idx_fits_files_object ON fits_files(object);
CREATE INDEX idx_fits_files_image_type_generic ON fits_files(image_type_generic);
CREATE INDEX idx_fits_files_create_time ON fits_files(create_time);

CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY,
    object TEXT NOT NULL UNIQUE,
    ra REAL,
    dec REAL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    target INTEGER,
    FOREIGN KEY (target) REFERENCES targets(id)
);

CREATE TABLE IF NOT EXISTS night_sessions (
    id INTEGER PRIMARY KEY,
    start_day TEXT NOT NULL UNIQUE
);

-- VIEWS

-- Create a view to get the list of all fits files that belong to a night session.
-- A night session is defined as the period from 12:00:00 of one day to 12:00:00 of the next day.
CREATE VIEW IF NOT EXISTS night_session_fits_files AS
SELECT 
    ns.id AS night_session_id,
    ff.id AS fits_file_id
FROM 
    night_sessions ns
JOIN 
    fits_files ff
ON 
    (
        DATE(DATETIME(ff.create_time, (ff.timezone_offset || ' hours'))) = ns.start_day 
        AND 
        TIME(DATETIME(ff.create_time, (ff.timezone_offset || ' hours'))) > '12:00:00'
    )
    OR 
    (
        DATE(DATETIME(ff.create_time, (ff.timezone_offset || ' hours'))) = DATE(ns.start_day, '+1 day')
        AND
        TIME(DATETIME(ff.create_time, (ff.timezone_offset || ' hours'))) <= '12:00:00'
    );

CREATE VIEW IF NOT EXISTS project_night_sessions AS
SELECT
    p.id AS project_id,
    ns.id AS night_session_id,
    ff.id AS fits_file_id
FROM
    projects p
JOIN
    targets t ON t.id = p.target
JOIN
    fits_files ff ON ff.object = t.object
JOIN 
    night_session_fits_files nsff ON nsff.fits_file_id = ff.id
JOIN 
    night_sessions ns ON ns.id = nsff.night_session_id
ORDER BY
    p.id, ns.start_day, ff.create_time;

-- TRIGGERS

-- When a new fits file is inserted, we need to check if it belongs to a night session.
-- If it does, we need to insert a new row in the night_sessions table.
CREATE TRIGGER IF NOT EXISTS insert_night_session
AFTER INSERT ON fits_files
WHEN
    NEW.timezone_offset IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM night_sessions WHERE start_day = 
        CASE WHEN TIME(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours'))) > '12:00:00' THEN
            DATE(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours')))
        ELSE 
            DATE(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours')), '-1 day')
        END
    )
BEGIN
    INSERT OR IGNORE INTO night_sessions (start_day)
    VALUES (
        CASE WHEN TIME(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours'))) > '12:00:00' THEN
            DATE(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours')))
        ELSE 
            DATE(DATETIME(NEW.create_time, (NEW.timezone_offset || ' hours')), '-1 day')
        END
    );
END;

-- When a new fits file is inserted, we need to check if the imaged object is already listed as a target.
-- If it is not, we need to insert a new row in the targets table at the position of this image.
CREATE TRIGGER IF NOT EXISTS insert_target
AFTER INSERT ON fits_files
WHEN 
    NEW.object IS NOT NULL
    AND NEW.ra IS NOT NULL
    AND NEW.dec IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM targets WHERE object = NEW.object)
    AND LOWER(NEW.imagetype) NOT LIKE '%flat%'
    AND LOWER(NEW.imagetype) NOT LIKE '%bias%'
    AND LOWER(NEW.imagetype) NOT LIKE '%dark%'
BEGIN
    INSERT OR IGNORE INTO targets (object, ra, dec)
    VALUES (NEW.object, NEW.ra, NEW.dec);
END;

CREATE TRIGGER IF NOT EXISTS create_projects
AFTER INSERT ON targets
BEGIN
    INSERT OR IGNORE INTO projects (name, target)
    VALUES (NEW.object, NEW.id);
END;