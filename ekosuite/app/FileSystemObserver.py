import asyncio
from threading import Thread
from .AppDB import AppDB
from .DataStream import DataStream
from ekosuite.plugins.model.project.ProjectDB import ProjectDB

class FileSystemImageChangeListener:
    def __init__(self, listen):
        self._listen = listen
    
    def listen(self, image):
        self._listen(image)

class FileSystemObserver:
    def __init__(self, db: AppDB, listeners: set[FileSystemImageChangeListener] = set()):
        self._db = db
        self._folderObservers = dict[str, DataStream]()
        self._listeners = listeners
        self._projectDB = ProjectDB(self._db)
        self._activeThreads = dict[str, Thread]()
        self.setupObservers()

    def __del__(self):
        for folder, observer in self._folderObservers.items():
            if observer is not None:
                observer.stop()
        for thread in self._activeThreads.values():
            thread.join()
        self._folderObservers.clear()
        self._activeThreads.clear()
    
    def setupObservers(self):
        for folder in self._projectDB.selectedFolders:
            if self._folderObservers.get(folder) is None:
                self._folderObservers[folder] = DataStream(directory=folder)
                self._folderObservers[folder].observe(lambda image: self.listen(image), observeInitial=True)
                def run_scout():
                    asyncio.run(self._projectDB.scout(folder, progress=lambda p: print(p)))

                scout_thread = Thread(target=run_scout)
                scout_thread.start()
                self._activeThreads[folder] = scout_thread
        for folder in self._folderObservers.keys():
            if folder not in self._projectDB.selectedFolders:
                self._folderObservers.pop(folder)
                self._activeThreads[folder].join()
    
    def listen(self, image):
        listeners = self._listeners.copy()
        for listener in listeners:
            listener.listen(image)
    
    def addListener(self, listener: FileSystemImageChangeListener):
        self._listeners.add(listener)
    
    def removeListener(self, listener: FileSystemImageChangeListener):
        self._listeners.remove(listener)