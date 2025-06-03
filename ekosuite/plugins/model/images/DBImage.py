from .Image import Image
from .ImageData import ImageData
from .FITSImage import FITSImage
from .XISFImage import XISFImage
from ekosuite.app.AppDB import AppDB
from datetime import datetime

class DBImage(Image):
    def __init__(self, id: int, db: AppDB):
        super().__init__()
        self._db = db
        self._id = id
    
    @property
    def image_data(self) -> ImageData:
        if self.filename.split(".")[-1] == "fits":
            image_data = FITSImage(self.filename).image_data
        elif self.filename.split(".")[-1] == "xisf":
            image_data = XISFImage(self.filename).image_data
        else:
            raise ValueError(f"Unsupported image format: {self.filename}")
        return image_data

    @property
    def filename(self) -> str:
        result = self._db.conn.cursor().execute("SELECT filename FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def create_time(self) -> datetime:
        result = self._db.conn.cursor().execute("SELECT create_time FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return datetime.fromisoformat(result[0])
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")
    
    @property
    def latitude(self) -> float:
        result = self._db.conn.cursor().execute("SELECT lat FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")
    
    @property
    def longitude(self) -> float:
        result = self._db.conn.cursor().execute("SELECT lon FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def image_width(self) -> int:
        result = self._db.conn.cursor().execute("SELECT image_width FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def image_height(self) -> int:
        result = self._db.conn.cursor().execute("SELECT image_height FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def pixel_size(self) -> float:
        result = self._db.conn.cursor().execute("SELECT pixel_size FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def object(self) -> str:
        result = self._db.conn.cursor().execute("SELECT object FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def ra(self) -> float:
        result = self._db.conn.cursor().execute("SELECT ra FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def dec(self) -> float:
        result = self._db.conn.cursor().execute("SELECT dec FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")
    
    @property
    def instrument(self) -> str:
        result = self._db.conn.cursor().execute("SELECT instrument FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def telescope(self) -> str:
        result = self._db.conn.cursor().execute("SELECT telescope FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def filter(self) -> str | None:        
        result = self._db.conn.cursor().execute("SELECT filter FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def imagetype(self) -> str:
        result = self._db.conn.cursor().execute("SELECT imagetype FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def exptime(self) -> float:
        result = self._db.conn.cursor().execute("SELECT exptime FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")

    @property
    def focal_length(self) -> float | None:        
        result = self._db.conn.cursor().execute("SELECT focal_length FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def temperature(self) -> float | None: 
        result = self._db.conn.cursor().execute("SELECT temperature FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def sensor_temperature(self) -> float | None:
        result = self._db.conn.cursor().execute("SELECT sensor_temperature FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def gain(self) -> float | None:
        result = self._db.conn.cursor().execute("SELECT gain FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def bias(self) -> float | None:
        result = self._db.conn.cursor().execute("SELECT bias FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def airmass(self) -> float | None:
        result = self._db.conn.cursor().execute("SELECT airmass FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]

    @property
    def mpsas(self) -> float | None:
        result = self._db.conn.cursor().execute("SELECT mpsas FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        return result[0]
    
    @property
    def scale(self) -> float:
        result = self._db.conn.cursor().execute("SELECT scale FROM fits_files WHERE id = ?", (self._id,)).fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Image with ID {self._id} not found in database.")