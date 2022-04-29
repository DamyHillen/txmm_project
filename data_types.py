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

    def to_dict(self):
        return {
            "years": self.years,
            # "loc_names": self.loc_names,
            "countries": self.countries,
            "text": self.text,
            "composer": self.composer,
        }

    def __iter__(self):
        yield self.years
        yield self.countries
        yield self.text
        yield self.composer

    def filter_years(self, start: int, end: int) -> int:
        to_remove: List[int] = []

        for i, year in enumerate(self.years):
            if not (start <= year <= end):
                to_remove.append(i)

        for i in reversed(to_remove):
            self.years.pop(i)

        return len(self.years)


def temporospatial_from_json(json: dict) -> TemporospatialEntry:
    return TemporospatialEntry(**json)
