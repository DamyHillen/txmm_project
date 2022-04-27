from typing import *
import datetime
import logging
import copy

from pygal_maps_world.maps import World
import matplotlib.pyplot as plt
from pygal.style import Style
import numpy as np

from DataCollector import DataCollector


# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/main.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False

ORDER = [
    ("Medieval", "List of medieval composers", (500, 1400)),
    ("Renaissance", "List of Renaissance composers", (1400, 1600)),
    ("Baroque", "List of Baroque composers", (1600, 1760)),
    ("Classical", "List of Classical era composers", (1730, 1820)),
    ("Romantic", "List of Romantic composers", (1815, 1910)),
    ("Modernist", "List of modernist composers", (1890, 1950)),
    ("Postmodernist", "List of postmodernist composers", (1930, datetime.datetime.now().year))
    # ("20th century", "List of 20th-century classical composers", (1901, 2000)),
    # ("21st century", "List of 21st-century classical composers", (2001, datetime.datetime.now().year))
]


def main():
    data_collector = DataCollector()
    temporospatial_data, countries, country_codes = data_collector.get_temporospatial()
    filtered = filter_outliers(temporospatial_data)

    scatter_eras(filtered)
    render_map(filtered, countries, country_codes)

    pass


def filter_outliers(temporospatial_data: dict) -> dict:  # TODO: Make it work
    x = copy.deepcopy(temporospatial_data)
    years: Dict[str, Dict[str, Any]] = {}

    for era, entries in x.items():
        years[era] = {"years": []}
        for entry in entries:
            years[era]["years"].extend(entry.years)
        years[era]["mean"] = np.mean(years[era]["years"])
        years[era]["median"] = np.median(years[era]["years"])
        years[era]["std"] = np.std(years[era]["years"])
        del years[era]["years"]

        for entry in entries:
            for year in entry.years:
                if abs(year - years[era]["median"]) > 0.125 * years[era]["std"]:
                    while year in entry.years:
                        entry.years.remove(year)
            if len(entry.years) == 0:
                entries.remove(entry)

    return x


def scatter_eras(filtered_data: dict):
    for i, (label, link, (lower, upper)) in enumerate(ORDER):
        entries = filtered_data[link]
        ys = []
        for years, locations, sentence, composer in entries:
            ys.extend([y for y in years])
        med = np.median(ys)
        plt.scatter(ys, i*np.ones(len(ys)), alpha=0.02, label=f"{i}: {label}", marker='|')
        plt.vlines(x=[lower, upper], ymin=i-0.1, ymax=i+0.1, linewidth=2, colors='k')
        plt.scatter(med, i, color='k', marker='*')
    plt.legend()
    plt.xlim((750, 2022))
    plt.show()


def render_map(filtered, countries, country_codes):
    custom_style = Style(colors=(
        "#665544",
    ))
    worldmap = World(style=custom_style)
    worldmap.add("Countries", [country_codes[c] for c in countries if c in country_codes], color='black')

    # Best way to render?
    worldmap.render_to_file("data/maps/map.svg")
    worldmap.render_to_png("data/maps/map.png")
    worldmap.render_in_browser()


if __name__ == "__main__":
    main()
