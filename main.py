from DataCollector import DataCollector
from Processor import Processor
import visualization
import datetime
import logging

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
    ("Postmodernist", "List of postmodernist composers", (1930, datetime.datetime.now().year)),
    # ("20th century", "List of 20th-century classical composers", (1901, 2000)),
    # ("21st century", "List of 21st-century classical composers", (2001, datetime.datetime.now().year))
]


def main():
    processor = Processor()
    data_collector = DataCollector(processor=processor)

    temporospatial_data, countries, country_codes = data_collector.get_temporospatial()
    filtered = processor.filter_outliers(temporospatial_data)

    visualization.scatter_eras(filtered, ORDER)
    visualization.render_map(filtered, countries, country_codes)

    pass  # For a debugging breakpoint


if __name__ == "__main__":
    main()
