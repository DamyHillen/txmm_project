from urllib.request import urlopen
from bs4 import BeautifulSoup
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

# Scraper
# main_page = wikipedia.WikipediaPage(title='List of classical music composers by era')
# links = set(link for link in main_page.links if re.match("List of .* composers$", link) and not re.match(".*-era.*", link))


def renaissance_parser(era_pages: dict, link: str) -> list:
    return []


def plain_list_parser(era_pages: dict, link: str) -> list:
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
    "List of Renaissance composers": renaissance_parser,
    "List of postmodernist composers": plain_list_parser,
    "List of Baroque composers": plain_list_parser,
    "List of Classical era composers": plain_list_parser,
    "List of modernist composers": plain_list_parser,
    "List of medieval composers": table_parser,
    "List of 20th-century classical composers": table_parser,
    "List of 21st-century classical composers": table_parser
}

era_pages = {link: {} for link in links}
for link, parser in links.items():
    era_pages[link]['page'] = wikipedia.WikipediaPage(title=link)
    # era_pages[link]['links'] = era_pages[link]['page'].links
    era_pages[link]['bsoup'] = BeautifulSoup(urlopen(era_pages[link]['page'].url), 'html.parser')

    result = parser(era_pages, link)

    print(f"{link} has {len(result)} composers")
    # for i, table in enumerate(era_pages[link]['tables']):
    #


pass
