from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from tqdm import tqdm
import numpy as np
import wikipedia
import logging
import msgpack
import re
import os

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


def main():
    parser_per_link = {
        "List of Renaissance composers": plain_list_parser,
        "List of postmodernist composers": plain_list_parser,
        "List of Baroque composers": plain_list_parser,
        "List of Classical era composers": plain_list_parser,
        "List of modernist composers": plain_list_parser,
        "List of medieval composers": table_parser,
        "List of 20th-century classical composers": table_parser,
        "List of 21st-century classical composers": table_parser,
        "List of Romantic composers": table_parser
    }

    composers_per_link = load_composers(parser_per_link)
    preprocessing(composers_per_link)

    pass


def load_composers(parser_per_link: dict):
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    if not os.path.isfile("./data/scraped_data"):
        logger.info("Scraping data from web...")
        composers = get_parsed_data(parser_per_link)
        load_composer_texts(composers)
        with open("./data/scraped_data", "wb") as file:
            file.write(msgpack.packb(composers))
    else:
        logger.info("Loading existing data...")
        with open("./data/scraped_data", "rb") as file:
            composers = msgpack.unpackb(file.read())

    logger.info("Data loaded!")

    return composers


def load_composer_texts(composers_per_link: dict):
    for link, composers in composers_per_link.items():
        pbar = tqdm(total=len(composers), desc=f"Loading texts for composers in {link}")
        to_remove = []
        for composer in composers:
            try:
                bsoup = BeautifulSoup(urlopen(wikipedia.WikipediaPage(title=composer).url), 'html.parser')
                composers_per_link[link][composer] = " ".join([par.text.strip() for par in bsoup.find_all("p")])
            except:
                to_remove.append(composer)

            pbar.update(1)

        pbar.close()

        for c in to_remove:
            del composers_per_link[link][c]


def get_parsed_data(parser_per_link: dict) -> dict:
    era_pages = {link: {} for link in parser_per_link}
    pbar = tqdm(total=len(parser_per_link))
    pbar.set_description("Retrieving composer names")
    for link, parser in parser_per_link.items():
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
    # table_rows = [t for t in tables if len(t) > 70]

    composers = []


    if len(table_rows) > 150:
        for row in table_rows:
            cells = row.find_all('a')

            if cells and len(row.find_all('td')) > 2:
                composers.append(cells[0].contents[0].strip())
    return composers


def preprocessing(composers_per_link: dict):
    for link, composers in composers_per_link.items():
        pbar = tqdm(total=len(composers), desc=f"Preprocessing texts of composers in {link}")

        for composer in composers:
            text = composers[composer]

            sentences = sentence_tokenize_text(text)

            composers[composer] = {
                "text": text,
                "sentences": sentences
            }

            pbar.update(1)
        pbar.close()


def sentence_tokenize_text(text: str) -> list:
    text = re.sub(r"\[\d+\]", " ", text)     # Removing citations and quotes
    text = re.sub(r"\s+", " ", text)         # Replacing all whitespace with a single space
    sentences = re.split(r"[\.!\?] ", text)  # Splitting after . ! or ? followed by a space
    return sentences


if __name__=="__main__":
    main()
