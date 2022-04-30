from DataCollector import DataCollector
from Processor import Processor
import visualization
import datetime
import logging
import os

if os.path.isfile("./logs/main.log"):
    os.remove("./logs/main.log")

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/main.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False

ORDER = [
    ("Medieval", "List of medieval composers", (500, 1400), 'tab:blue'),
    ("Renaissance", "List of Renaissance composers", (1400, 1600), 'tab:orange'),
    ("Baroque", "List of Baroque composers", (1600, 1760), 'tab:green'),
    ("Classical", "List of Classical era composers", (1730, 1820), 'tab:red'),
    ("Romantic", "List of Romantic composers", (1815, 1910), 'tab:purple'),
    ("Modernist", "List of modernist composers", (1890, 1950), 'tab:brown'),
    ("Postmodernist", "List of postmodernist composers", (1930, datetime.datetime.now().year), 'tab:pink'),
    # ("20th century", "List of 20th-century classical composers", (1901, 2000), 'black'),
    # ("21st century", "List of 21st-century classical composers", (2001, datetime.datetime.now().year), 'cyan')
]


def main():
    processor = Processor()
    data_collector = DataCollector(processor=processor)

    logger.info("Retrieving temporospatial data")
    temporospatial_data, countries, country_codes = data_collector.get_temporospatial()
    logger.info("Filtering outliers")
    filtered = processor.filter_outliers(temporospatial_data, ORDER)

    logger.info("visualization.scatter_eras()")
    visualization.scatter_eras(filtered, ORDER)
    logger.info("visualization.render_map()")
    visualization.render_maps(filtered, country_codes, ORDER)

    pass  # For a debugging breakpoint


if __name__ == "__main__":
    main()
