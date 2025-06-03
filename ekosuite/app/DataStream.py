from ekosuite.plugins.model.images.FITSImage import FITSImage
from ekosuite.plugins.model.images.Image import Image
import watchdog.events as wde
import watchdog.observers as wdo
from typing import Callable
import threading

from ekosuite.plugins.model.images.XISFImage import XISFImage

class DataStream(wde.FileSystemEventHandler):
    def __init__(self, directory: str):
        self._latest: Image | None = None
        self._observers: list[Callable[[Image], None]] = []
        self._lock = threading.Lock()
        self._fileObserver = wdo.Observer()
        self._fileObserver.schedule(self, directory, recursive=True)
        self._fileObserver.start()
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.fits'):
            self.receive(event.src_path)
    
    def receive(self, source: str):
        """
        Receives a new FITS image from the source.
        """
        with self._lock:
            if len(self._observers) == 0:
                return
            if source.lower().endswith('.xisf'):
                self._latest = XISFImage(source)
            else:
                self._latest = FITSImage(source)
            for observer in self._observers:
                try:
                    observer(self._latest)
                except Exception as e:
                    print(f"Error in observer callback: {e}")
    
    def observe(self, callback: Callable[[Image], None], observeInitial: bool = True):
        """
        Observes the latest FITS image.
        """
        with self._lock:
            if isinstance(self._latest, Image) and observeInitial:
                callback(self._latest)
            self._observers.append(callback)

    def stop(self):
        """
        Stops the file observer.
        """
        self._fileObserver.stop()
        self._fileObserver.join()
