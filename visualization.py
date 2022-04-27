from pygal_maps_world.maps import World
import matplotlib.pyplot as plt
from pygal.style import Style
import numpy as np
import logging

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/visualization.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


def scatter_eras(filtered_data: dict, order: list):
    logger.info(f"Scattering the data using order {order}")
    for i, (label, link, (lower, upper)) in enumerate(order):
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
    logger.info("Rendering map(s)!")
    custom_style = Style(colors=(
        "#665544",
    ))
    worldmap = World(style=custom_style)
    worldmap.add("Countries", [country_codes[c] for c in countries if c in country_codes], color='black')

    # Best way to render?
    worldmap.render_to_file("data/maps/map.svg")
    worldmap.render_to_png("data/maps/map.png")
    # worldmap.render_in_browser()
