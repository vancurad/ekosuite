from datetime import datetime
from ekosuite.plugins.model.images.Image import Image

class NightSession:
    
    def __init__(self, date: str, images: list[Image]):
        self.date = date
        self.images = images