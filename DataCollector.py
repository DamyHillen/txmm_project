from bs4.element import NavigableString
from Processor import Processor
from urllib.request import urlopen
from bs4 import BeautifulSoup
from data_types import *
from tqdm import tqdm
from typing import *
import wikipedia
import logging
import msgpack
import os

if os.path.isfile("./logs/data_collection.log"):
    os.remove("./logs/data_collection.log")

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/data_collection.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


class DataCollector:
    def __init__(self, processor):
        self.parser_per_link = {
            "List of Renaissance composers": self.plain_list_parser,
            "List of postmodernist composers": self.plain_list_parser,
            "List of Baroque composers": self.plain_list_parser,
            "List of Classical era composers": self.plain_list_parser,
            "List of modernist composers": self.plain_list_parser,
            "List of medieval composers": self.table_parser,
            "List of 20th-century classical composers": self.table_parser,
            "List of 21st-century classical composers": self.table_parser,
            "List of Romantic composers": self.table_parser
        }

        self.processor = processor if processor else Processor()

    def get_temporospatial(self) -> Tuple[dict, List[str], dict]:
        temporospatial_data = get_data(
            file_name="temporospatial_data",
            per_link=lambda a: [temporospatial_from_json(x) for x in a]
        )
        country_data = get_data(
            file_name="countries_found"
        )

        if country_data:
            countries, country_codes = country_data

        if not temporospatial_data:
            composers_per_link = get_data("scraped_data")
            if not composers_per_link:
                composers_per_link = self.scrape_composers()
            store_data(composers_per_link, "scraped_data")

            preprocessed = self.processor.preprocess(composers_per_link)
            temporospatial_data, countries, country_codes = self.processor.filter_temporospatial(preprocessed)
            store_data(temporospatial_data, "temporospatial_data", per_link=lambda a: [x.to_dict() for x in a])
            store_data([countries, country_codes], "countries_found")

        del temporospatial_data["List of 20th-century classical composers"]
        del temporospatial_data["List of 21st-century classical composers"]

        return temporospatial_data, countries, country_codes

    def scrape_composers(self):
        composers = self.get_parsed_data()
        self.load_composer_texts(composers)

        return composers

    def get_parsed_data(self) -> dict:
        era_pages = {link: {} for link in self.parser_per_link}
        pbar = tqdm(total=len(self.parser_per_link))
        pbar.set_description("Retrieving composer names")
        for link, parser in self.parser_per_link.items():
            logger.info(f"Retrieving page of link \'{link}\'")
            era_pages[link]['page'] = wikipedia.WikipediaPage(title=link)
            logger.info(f"Retrieving bsoup of link \'{link}\'")
            era_pages[link]['bsoup'] = BeautifulSoup(urlopen(era_pages[link]['page'].url), 'html.parser')

            logger.info(f"Parsing page of link \'{link}\' using {parser}")
            era_pages[link] = {composer: "" for composer in parser(era_pages, link)}

            logger.info(f"{link} has {len(era_pages[link])} composers")

            pbar.update(1)
        pbar.close()

        return era_pages

    @staticmethod
    def load_composer_texts(composers_per_link: dict):
        for link, composers in composers_per_link.items():
            pbar = tqdm(total=len(composers), desc=f"Loading texts for composers in {link}")
            to_remove = []
            for composer in composers:
                try:
                    bsoup = BeautifulSoup(urlopen(wikipedia.WikipediaPage(title=composer).url), parser='html.parser')
                    composers_per_link[link][composer] = " ".join([par.text.strip() for par in bsoup.find_all("p")])
                except:
                    to_remove.append(composer)

                pbar.update(1)
            pbar.close()

            for c in to_remove:
                del composers_per_link[link][c]

    @staticmethod
    def plain_list_parser(era_pages: dict, link: str) -> list:
        ul_items = era_pages[link]['bsoup'].find_all('ul')

        composers = []

        for item in ul_items:
            hrefs = item.find_all("a")
            if hrefs:
                for elem in hrefs:
                    if elem.contents:
                        name = elem.contents[0]
                        if type(name) is NavigableString:
                            name = str(name)
                            if len(name) and '[' not in name:
                                composers.append(name)

        composer = {
            "List of Renaissance composers": "Nicholas Dáll Pierce",
            "List of postmodernist composers": "Philip Glass",
            "List of Baroque composers": "Santa della Pietà",
            "List of Classical era composers": "Oscar I of Sweden",
            "List of modernist composers": "William Walton",
        }[link]
        i = composers.index(composer)
        return composers[:i + 1]

    @staticmethod
    def table_parser(era_pages: dict, link: str) -> list:
        tables = [t.find_all('tr') for t in era_pages[link]['bsoup'].find_all('table')]
        # table_rows = tables[np.argmax([len(t) for t in tables])]
        table_rows = [t for t in tables if len(t) > 70]

        composers = []

        for rows in table_rows:
            for row in rows:
                cells = row.find_all('a')

                if cells and len(row.find_all('td')) > 2:
                    composers.append(cells[0].contents[0].strip())
        return composers


def get_data(file_name: str, per_link=None):
    data = {}
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    if os.path.isfile(f"./data/{file_name}"):
        with open(f"./data/{file_name}", "rb") as file:
            data = msgpack.unpackb(file.read())
        logger.info(f"Retrieved data from ./data/{file_name}")
    else:
        logger.info(f"Could not retrieve data from ./data/{file_name}")

    if data and per_link:
        data = {link: per_link(data[link]) for link in data.keys()}
    return data


def store_data(data, file_name: str, per_link=None):
    if per_link:
        data = {link: per_link(data[link]) for link in data.keys()}
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    with open(f"./data/{file_name}", "wb") as file:
        file.write(msgpack.packb(data))
