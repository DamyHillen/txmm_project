from bs4.element import NavigableString
from urllib.request import urlopen
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from geotext import GeoText
from tqdm import tqdm
import numpy as np
import wikipedia
import datetime
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

ORDER = [
    ("Medieval", "List of medieval composers", (500, 1400)),
    ("Renaissance", "List of Renaissance composers", (1400, 1600)),
    ("Baroque", "List of Baroque composers", (1600, 1760)),
    ("Classical", "List of Classical era composers", (1730, 1820)),
    ("Romantic", "List of Romantic composers", (1815, 1910)),
    ("Modernist", "List of modernist composers", (1890, 1950)),
    ("Postmodernist", "List of postmodernist composers", (1930, datetime.datetime.now().year)),
    ("20th century", "List of 20th-century classical composers", (1901, 2000)),
    ("21st century", "List of 21st-century classical composers", (2001, datetime.datetime.now().year))
]

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

    filtered = get_data("filtered_years")
    if not filtered:
        composers_per_link = get_data("scraped_data")
        if not composers_per_link:
            composers_per_link = scrape_composers(parser_per_link)
            store_data(composers_per_link, "scraped_data")

        preprocessing(composers_per_link)
        filtered = filter_years(composers_per_link)
        store_data(filtered, "filtered_years")

    scatter_eras(filtered)
    pass


def scrape_composers(parser_per_link: dict):
    composers = get_parsed_data(parser_per_link)
    load_composer_texts(composers)

    return composers


def get_data(file_name: str):
    data = None
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    if os.path.isfile(f"./data/{file_name}"):
        with open(f"./data/{file_name}", "rb") as file:
            data = msgpack.unpackb(file.read())
        logger.info(f"Retrieved data from ./data/{file_name}")
    else:
        logger.info(f"Could not retrieve data from ./data/{file_name}")

    return data


def store_data(data, file_name: str):
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    with open(f"./data/{file_name}", "wb") as file:
        file.write(msgpack.packb(data))


def load_composer_texts(composers_per_link: dict):
    for link, composers in composers_per_link.items():
        pbar = tqdm(total=len(composers), desc=f"Loading texts for composers in {link}")
        to_remove = []
        for composer in composers:
            if "Johann Sebastian" in composer:
                pass
            try:
                bsoup = BeautifulSoup(urlopen(wikipedia.WikipediaPage(title=composer).url), parser='html.parser')
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

    composer = {
        "List of Renaissance composers": "Nicholas Dáll Pierce",
        "List of postmodernist composers": "Philip Glass",
        "List of Baroque composers": "Santa della Pietà",
        "List of Classical era composers": "Oscar I of Sweden",
        "List of modernist composers": "William Walton",
    }[link]
    i = composers.index(composer)
    return composers[:i+1]


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


def filter_years(composers_per_link: dict) -> dict:
    x = {link: [] for link in composers_per_link}

    for link in x:
        pbar = tqdm(total=sum([len(composers_per_link[link][composer]["sentences"]) for composer in composers_per_link[link]]), desc=f"Filtering years and locations for {link}")
        for composer in composers_per_link[link]:
            for sentence in composers_per_link[link][composer]["sentences"]:
                years = re.findall("([12]?[0-9]{3})( BC| B.C.| BC.)?", sentence)  # TODO: Fix this damn regex (also: don't forget dates 0-1000)
                years = [int(y) for y, bc in years if len(bc) == 0 and int(y) <= datetime.datetime.now().year]
                if years:
                    locations = []

                    for w in range(1, 4):
                        for i in range(len(sentence.split(" ")) - (w - 1)):
                            gt = GeoText(" ".join(sentence.split(" ")[i:i+w]))
                            extracted_locs = gt.cities if gt.cities else gt.countries
                            for loc in extracted_locs:
                                if loc not in locations:
                                    locations.append(loc)
                    if locations:
                        x[link].append((years, locations, sentence))
                pbar.update(1)
        pbar.close()

    return x


def scatter_eras(filtered_data: dict):
    for i, (label, link, (lower, upper)) in enumerate(ORDER):
        entries = filtered_data[link]
        ys = []
        for entry in entries:
            years, locations, sentence = entry
            ys.extend([y for y in years])
        med = np.median(ys)
        plt.scatter(ys, i*np.ones(len(ys)), alpha=0.02, label=f"{i}: {label}", marker='|')
        plt.vlines(x=[lower, upper], ymin=i-0.1, ymax=i+0.1, linewidth=2, colors='k')
        plt.scatter(med, i, color='k', marker='*')
    plt.legend()
    plt.xlim((750, 2022))
    plt.show()


if __name__=="__main__":
    main()
