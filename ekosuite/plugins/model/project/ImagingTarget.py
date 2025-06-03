class ImagingTarget:
    """
    Class representing an imaging target in a project.
    """

    def __init__(self, id: int, name: str, dec: float, ra: float):
        self.id = id
        self.name = name
        self.dec = dec
        self.ra = ra