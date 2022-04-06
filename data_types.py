from dataclasses import dataclass
from geopy import Nominatim
from typing import *

nominatim = Nominatim(user_agent="GetLoc")


@dataclass
class Composer:
    name: str
    era: str
    text: str
    sentences: List[str]


@dataclass
class TemporospatialEntry:
    years: List[int]
    loc_names: List[str]
    text: str
    composer: str

    loc_coords: List[Tuple[float, float]] = None

    def to_dict(self):
        return {
            "years": self.years,
            "loc_names": self.loc_names,
            "text": self.text,
            "composer": self.composer,
            "loc_coords": self.loc_coords
        }

    def set_coords(self):
        locs = [nominatim.geocode(loc) for loc in self.loc_names]
        self.loc_coords = [(l.latitude, l.longitude) for l in locs]

    def __iter__(self):
        yield self.years
        yield self.loc_names
        yield self.text
        yield self.composer


def temporospatial_from_json(json: dict) -> TemporospatialEntry:
    return TemporospatialEntry(**json)
