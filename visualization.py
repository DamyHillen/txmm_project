from pygal_maps_world.maps import World
import matplotlib.pyplot as plt
from matplotlib import colors
from pygal.style import Style
from data_types import *
from tqdm import tqdm
import numpy as np
import logging
import os

if os.path.isfile("./logs/visualization.log"):
    os.remove("./logs/visualization.log")

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/visualization.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


def scatter_eras(filtered_data: dict, order: list):
    logger.info(f"Scattering the data using order {order}")
    start = order[0][2][0]
    end = order[-1][2][1]

    for i, (label, link, (lower, upper), color) in enumerate(order):
        entries = filtered_data[link]
        ys = []
        for years, locations, sentence, composer in entries:
            ys.extend([y for y in years])
        med = np.median(ys)
        plt.scatter(ys, i*np.ones(len(ys)), alpha=(upper - lower)/5000, color=color, label=f"{i}: {label}", marker='|')
        plt.vlines(x=[lower, upper], ymin=i-0.1, ymax=i+0.1, linewidth=2, colors='k')
        plt.scatter(med, i, color='k', marker='*', label="Data median" if i == 6 else None)
    leg = plt.legend()
    for lh in leg.legendHandles:
        if not lh._label == "Data median":
            lh.set(alpha=1, linewidth=5)  # Make legend icons properly visible
    plt.xlim((start, end))
    plt.xlabel("Year")
    plt.ylabel("Era number")
    plt.show()


def render_maps(filtered_data: dict, country_codes: dict, order: list):
    logger.info("Rendering maps!")
    custom_style = Style(colors=tuple(colors.colorConverter.colors[c] for _, _, _, c in order))  # plt colors to hex
    start = order[0][2][0]
    end = order[-1][2][1]
    era_names = [e[0] for e in order]

    era_per_year_per_country = {}

    for name, link, (lower, upper), color in order:
        entries: List[TemporospatialEntry] = filtered_data[link]

        for entry in entries:
            years, countries, _, _ = entry

            for country in countries:
                if country not in era_per_year_per_country:
                    era_per_year_per_country[country] = {
                        name: {} for name in era_names
                    }
                d = era_per_year_per_country[country][name]
                for year in years:
                    if year not in d:
                        d[year] = 0
                    d[year] += 1

    if not os.path.isdir("./data/maps"):
        os.mkdir("./data/maps")

    last_era: dict = {}

    pbar = tqdm(total=end-start, desc=f"Creating maps for {end-start} years")
    for year in range(start, end+1):
        worldmap = World(style=custom_style)
        worldmap.title = f"Musical eras in {year}"
        for i, era in enumerate(era_names):
            for country in era_per_year_per_country.keys():
                if year in era_per_year_per_country[country][era]:
                    if country in country_codes:
                        code = country_codes[country]
                        if code not in last_era:
                            last_era[code] = i
                        else:
                            last_era[code] = max(last_era[code], i)

        if last_era:
            codes_per_era = {
                era: [] for era in era_names
            }
            latest_era = 0
            for code, era in last_era.items():
                latest_era = max(latest_era, era)
                codes_per_era[era_names[era]].append(code)

            for i in range(latest_era-1):
                codes_per_era[era_names[i]] = []

            for era in era_names:
                worldmap.add(era, codes_per_era[era])
            worldmap.render_to_png(f"data/maps/map_{year}.png")
        pbar.update(1)
    pbar.close()
