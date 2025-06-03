import os
import sqlite3

import os
import sqlite3
import threading
from queue import Queue, Empty

class AppDB:
    def __init__(self, folder=os.path.expanduser("~/.ekosuite/")):
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            # On Windows, set the folder as hidden
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(self.folder, FILE_ATTRIBUTE_HIDDEN)
        self.dbFile = os.path.join(self.folder, "ekosuite.sqlite")

        self.__conn: sqlite3.Connection = None
        self.queue = Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

        self._initialize_db()
    
    @property
    def conn(self) -> sqlite3.Connection:
        if self.__conn is None:
            raise ValueError("Database connection is not initialized.")
        return self.__conn

    def _initialize_db(self):
        def init():
            self.__conn = sqlite3.connect(self.dbFile, check_same_thread=False)
            cursor = self.__conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            self.__conn.commit()
            self.handleVersions()
        self.queue.put((init, None))

    def handleVersions(self):
        db_folder = os.path.join(os.path.dirname(__file__), "db")
        if not os.path.exists(db_folder):
            return

        files = os.listdir(db_folder)
        files.sort()
        for file_name in files:
            if file_name.endswith(".sql"):
                sqlStatement = os.path.join(db_folder, file_name)
                with open(sqlStatement, 'r') as sqlFile:
                    sqlScript = sqlFile.read()
                    self.__conn.executescript(sqlScript)
        self.__conn.commit()

    def _worker(self):
        while True:
            try:
                task, result_queue = self.queue.get()
                if task is None:  # Sentinel to stop the thread
                    break
                result = task()
                if result_queue:
                    result_queue.put(result)
            except Exception as e:
                if result_queue:
                    result_queue.put(e)

    def close(self):
        self.queue.put((None, None))  # Sentinel to stop the thread
        self.thread.join()
        if self.__conn:
            self.__conn.close()

    def execute(self, query, params=()) -> sqlite3.Cursor:
        result_queue = Queue()
        def task():
            try:
                cursor = self.__conn.cursor()
                result = cursor.execute(query, params)
                self.__conn.commit()
                return result
            except Exception as e:
                print(f"Interface error in query: {query}\n\nWith params: {params}\n\nResulting Exception: {e}")
                raise e
        
        self.queue.put((task, result_queue))
        return result_queue.get()

    def fetchall(self, query, params=()):
        result_queue = Queue()
        def task():
            cursor = self.__conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        self.queue.put((task, result_queue))
        return result_queue.get()

    def get(self, query, params=()):
        result_queue = Queue()
        def task():
            cursor = self.__conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        self.queue.put((task, result_queue))
        return result_queue.get()