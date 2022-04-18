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
    # loc_names: List[str]
    countries: List[str]
    text: str
    composer: str

    # loc_coords: List[Tuple[float, float]] = None

    def to_dict(self):
        return {
            "years": self.years,
            # "loc_names": self.loc_names,
            "countries": self.countries,
            "text": self.text,
            "composer": self.composer#,
            # "loc_coords": self.loc_coords
        }

    # def set_coords(self, loc_mapping: dict):
    #     self.loc_coords = []
    #     for loc in self.loc_names:
    #         if loc not in loc_mapping:
    #             l = nominatim.geocode(loc)
    #             loc_mapping[loc] = (l.latitude, l.longitude)
    #         self.loc_coords.append(loc_mapping[loc])

    def __iter__(self):
        yield self.years
        yield self.countries
        yield self.text
        yield self.composer


def temporospatial_from_json(json: dict) -> TemporospatialEntry:
    return TemporospatialEntry(**json)
