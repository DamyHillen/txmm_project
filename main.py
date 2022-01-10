from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from tqdm import tqdm
import numpy as np
import wikipedia
import logging
import msgpack
import re

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


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

    # Santa della Pietà exists in two lists. Keep last!
    for composer in ['William Walton', 'Philip Glass', 'Oscar I of Sweden', 'John IV of Portugal', 'Santa della Pietà']:
        if composer in composers:
            i = composers.index(composer)
            return composers[:i+1]
    return []


def table_parser(era_pages: dict, link: str) -> list:
    tables = [t.find_all('tr') for t in era_pages[link]['bsoup'].find_all('table')]
    table_rows = tables[np.argmax([len(t) for t in tables])]

    composers = []

    if len(table_rows) > 170:
        for row in table_rows:
            cells = row.find_all('a')
            if cells and len(row.find_all('td')) > 2:
                composers.append(cells[0].contents[0].strip())
    return composers


links = {
    "List of Renaissance composers": plain_list_parser,
    "List of postmodernist composers": plain_list_parser,
    "List of Baroque composers": plain_list_parser,
    "List of Classical era composers": plain_list_parser,
    "List of modernist composers": plain_list_parser,
    "List of medieval composers": table_parser,
    "List of 20th-century classical composers": table_parser,
    "List of 21st-century classical composers": table_parser
}

era_pages = {link: {} for link in links}
pbar = tqdm(total=len(links))
pbar.set_description("Retrieving composer names")
for link, parser in links.items():
    logger.info(f"Retrieving page of link \'{link}\'")
    era_pages[link]['page'] = wikipedia.WikipediaPage(title=link)
    logger.info(f"Retrieving bsoup of link \'{link}\'")
    era_pages[link]['bsoup'] = BeautifulSoup(urlopen(era_pages[link]['page'].url), 'html.parser')

    logger.info(f"Parsing page of link \'{link}\' using {parser}")
    era_pages[link]["composers"] = parser(era_pages, link)

    logger.info(f"{link} has {len(era_pages[link]['composers'])} composers")

    pbar.update(1)
pbar.close()


