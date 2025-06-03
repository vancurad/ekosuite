from ekosuite.app import AppDB
from .NightSession import NightSession
from .ImagingTarget import ImagingTarget

class ImagingProject:
    """
    Class representing an imaging project.
    """

    def __init__(self, id: int, name: str, target: ImagingTarget, sessions: list[NightSession]):
        self.id = id
        self.name = name
        self.sessions = sessions
        self.target = target