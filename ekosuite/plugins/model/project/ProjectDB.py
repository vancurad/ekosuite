from datetime import datetime
import json
import time
from typing import Callable, Iterable
from ekosuite.app.AppDB import AppDB
from ekosuite.plugins.model.images.FITSImage import FITSImage
from ekosuite.plugins.model.images.Image import Image
from ekosuite.plugins.model.images.XISFImage import XISFImage
from .ImagingProject import ImagingProject
from .ImagingTarget import ImagingTarget
from .NightSession import NightSession
from ekosuite.plugins.model.images.DBImage import DBImage
from sqlite3 import Cursor, Row
import os
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class FileReader:
    def __init__(self):
        self.executor = ThreadPoolExecutor(thread_name_prefix="FileReader", max_workers=os.cpu_count())  # Limit threads
        self.lock = threading.Lock()
        self.futures = []
        self.analyzed_files = []

    def _readImage(self, path: str):
        image = self._getFits(path)
        if image is None:
            return None
        try:
            return (
                    image.filename, 
                    image.create_time, 
                    image.latitude,
                    image.longitude,
                    image.timezone_offset,
                    image.image_width, 
                    image.image_height, 
                    image.pixel_size, 
                    image.scale, 
                    image.object, 
                    image.ra, 
                    image.dec, 
                    image.instrument,
                    image.telescope,
                    image.filter, 
                    image.imagetype, 
                    image.exptime, 
                    image.focal_length, 
                    image.temperature, 
                    image.sensor_temperature, 
                    image.gain, 
                    image.bias, 
                    image.mpsas, 
                    image.airmass
                )
        except Exception as e:
            return None
    
    def _getFits(self, path: str) -> Image | None:
        result = None
        try:
            if path.lower().endswith('.xisf'):
                result = XISFImage(path)
            else:
                result = FITSImage(path)
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None
        finally:
            return result

    def scout(self, foldername: str, known_files: set, progress: Callable[[float], None]) -> list[threading.Thread]:
        """Recursively scan directories and submit file reading tasks."""
        print(f"Scouting folder: {foldername}")

        for root, _, files in os.walk(foldername):
            for file in files:
                filepath = os.path.join(root, file)
                if file.lower().endswith(('.fit', '.fits', '.xisf')) and filepath not in known_files:
                    # Submit the file reading task to the thread pool
                    future = self.executor.submit(self._readImage, filepath)
                    with self.lock:
                        self.futures.append(future)
                        self.analyzed_files.append(filepath)

        return self.futures

class ProjectDB:
    def __init__(self, db: AppDB):
        self._db = db
        self._mainThread = None
        self._mainLoop = None
        self._fileReadLoop = None
        self._fileReadThread = None
        self._fileReader = FileReader()
    
    def __del__(self):
        if self._fileReadThread:
            self._fileReadThread.join()

    def allProjectNames(self) -> list[str]:
        """
        Get all projects from the database.
        :return: List of projects
        """
        return self._db.execute("SELECT name FROM projects ORDER BY name ASC").fetchall()

    def getProject(self, name: str) -> ImagingProject | None:
        cursor: Cursor = self._db.execute("SELECT id, name, target FROM projects WHERE name=?", (name,))
        row: Row = cursor.fetchone()
        if row:
            target = self._getImagingTarget(row[2])
            sessions = self._getSessionsForProject(row[0])
            return ImagingProject(row[0], row[1], target, sessions)
        return None
    
    async def insertImage(self, image: Image):
        await self._insertImagesToDb(
            [
                (
                    image.filename, 
                    image.create_time, 
                    image.latitude,
                    image.longitude,
                    image.timezone_offset,
                    image.image_width, 
                    image.image_height, 
                    image.pixel_size, 
                    image.scale, 
                    image.object, 
                    image.ra, 
                    image.dec, 
                    image.instrument,
                    image.telescope,
                    image.filter, 
                    image.imagetype, 
                    image.exptime, 
                    image.focal_length, 
                    image.temperature, 
                    image.sensor_temperature, 
                    image.gain, 
                    image.bias, 
                    image.mpsas, 
                    image.airmass
                )
            ]
        )
        self._udpateCalibrationFrameTimezones()

    def _getImagingTarget(self, targetId: int) -> ImagingTarget | None:
        cursor: Cursor = self._db.execute("SELECT id, object, ra, dec FROM imaging_targets WHERE id=?", (targetId,))
        row: Row = cursor.fetchone()
        if row:
            return ImagingTarget(row[0], row[1], row[2], row[3])
        return None

    def _getSessionsForProject(self, projectId: int) -> list[NightSession]:
        cursor: Cursor = self._db.execute("""
                    SELECT 
                        pns.project_id as project_id, 
                        pns.night_session_id as night_session_id, 
                        pns.fits_file_id,
                        ns.start_day as date,
                    FROM project_night_sessions pns
                    JOIN night_sessions ns ON pns.night_session_id = ns.id
                    WHERE pns.project_id=?
                    """, (projectId,))
        rows: list[Row] = cursor.fetchall()

        session_map = {}
        session_order = []
        for row in rows:
            session_id = row[1]
            image_id = row[2]
            if session_id:
                if session_id not in session_map:
                    session_order.append(session_id)
                    session_map[session_id] = NightSession(row[3], [])
                session_map[session_id].images.append(DBImage(image_id, self._db))
        return list(map(lambda session_id: session_map[session_id], session_order))

    async def scout(self, foldername: str, progress):
        start_time = datetime.now()
        print(f"Searching for files in {foldername}")
        all_files = self._db.execute("""
            SELECT filename FROM analyzed_files
            UNION
            SELECT filename FROM fits_files
        """).fetchall()
        if all_files is None:
            known_files = set()
        else:
            known_files = set(map(lambda f: f[0], all_files))

        # futures = self._scout(foldername, known_files, progress)
        self._fileReader.futures = []
        self._fileReader.analyzed_files = []
        futures = self._fileReader.scout(foldername, known_files, progress)
        print(f"{datetime.now() - start_time}: Aggregated list of {len(futures)} files. Analyzing ...")
        fits_files = []
        i = 0
        start_time = datetime.now()
        if len(futures) > 0:
            chunk_size = 1
            for future in as_completed(futures):
                result = future.result()
                if result:
                    fits_files.append(result)
                i = i + 1
                print(f"\r{(datetime.now() - start_time)}: Progress: {(i / len(futures) * 100):.2f} percent", end="")
                if (len(fits_files) > 0 and len(fits_files) % chunk_size == 0) or i == len(futures):
                    await self._insertImagesToDb(fits_files)
                    self._udpateCalibrationFrameTimezones()
                    # print(f"\n{(datetime.now() - start_time)}: Inserted chunk of {len(fits_files)} images to DB")
                    fits_files = []
        
        if len(self._fileReader.analyzed_files) > 0:
            self._db.execute("INSERT OR IGNORE INTO analyzed_files (filename) VALUES " + ",".join(["(?)"] * len(self._fileReader.analyzed_files)), self._fileReader.analyzed_files)

    async def _insertImagesToDb(self, images: list):
        if len(images) == 0:
            return
        # Build the SQL statement with multiple rows in the VALUES clause
        sql = """
        INSERT OR FAIL INTO fits_files (
            filename,
            create_time,
            lat,
            lon,
            timezone_offset,
            image_width,
            image_height,
            pixel_size,
            scale,
            object,
            ra,
            dec,
            instrument,
            telescope,
            filter,
            imagetype,
            exptime,
            focal_length,
            temperature,
            sensor_temperature,
            gain,
            bias,
            mpsas,
            airmass
        ) VALUES
        """ + ",".join(["(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"] * len(images))
        
        # Flatten the list of tuples for parameter substitution
        values = [
            item
            for image in images
            for item in image
        ]

        try:
            self._db.execute(sql, values)
        except Exception as e:
            print(e)
        finally:
            return
    
    def _udpateCalibrationFrameTimezones(self):
        statement = """
        UPDATE fits_files
        SET timezone_offset = (
            SELECT source.timezone_offset
                FROM fits_files AS source
                WHERE source.create_time BETWEEN DATETIME(create_time, '-12 hours') 
                    AND DATETIME(create_time, '+12 hours')
                    AND source.timezone_offset IS NOT NULL
                    AND source.instrument = instrument
                    AND (source.telescope = telescope OR image_type_generic NOT IN ('FLAT', 'MASTER FLAT'))
                    AND (source.filter = filter OR image_type_generic IN ('DARK', 'MASTER DARK', 'BIAS', 'MASTER BIAS'))
                ORDER BY ABS(DATETIME(source.create_time) - DATETIME(create_time))
                LIMIT 1
        )
        WHERE timezone_offset IS NULL;
        """
        try:
            self._db.execute(statement)
        except Exception as e:
            print(e)
        finally:
            return
    
    @property
    def selectedFolders(self) -> list[str]:
        existing_settings = self._db.execute("SELECT value FROM user_settings WHERE item = 'folders'").fetchone()
        if existing_settings is None:
            _ = self._db.execute("INSERT INTO user_settings (item, value) VALUES (?, ?)", ("folders", "[]"))
            return []
        selected_folders: list | None = json.loads(existing_settings[0])
        if selected_folders is None:
            selected_folders = []
        return selected_folders
    
    @selectedFolders.setter
    def selectedFolders(self, newValues: list[str]):
        _ = self._db.execute("INSERT OR REPLACE INTO user_settings (item, value) VALUES (?, ?)", ("folders", json.dumps(newValues)))