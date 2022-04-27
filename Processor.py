from LocationParser import LocationParser
from data_types import *
from tqdm import tqdm
import numpy as np
import datetime
import logging
import copy
import re

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/processor.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


class Processor:
    def preprocess(self, composers_per_link: dict) -> dict:
        result = {
            link: [] for link in composers_per_link.keys()
        }

        for link, composers in composers_per_link.items():
            pbar = tqdm(total=len(composers), desc=f"Preprocessing texts of composers in {link}")
            logger.info(f"Preprocessing texts of composers in \'{link}\'")

            for composer in composers:
                text = composers[composer]
                sentences = self.sentence_tokenize_text(text)
                result[link].append(Composer(composer, link, text, sentences))

                pbar.update(1)
            pbar.close()

        return result

    @staticmethod
    def sentence_tokenize_text(text: str) -> list:
        text = re.sub(r"\[\d+\]", " ", text)  # Removing citations and quotes
        text = re.sub(r"\s+", " ", text)  # Replacing all whitespace with a single space
        sentences = re.split(r"[\.!\?] ", text)  # Splitting after . ! or ? followed by a space
        return sentences

    @staticmethod
    def filter_temporospatial(composers_per_link: dict) -> Tuple[dict, List[str], dict]:
        loc_parser = LocationParser()

        countries_found = set()
        x = {link: [] for link in composers_per_link}

        for link in x:
            pbar = tqdm(total=sum([len(composer.sentences) for composer in composers_per_link[link]]),
                        desc=f"Filtering years and locations for {link}")
            logger.info(f"Filtering years and locations for \'{link}\'")
            for composer in composers_per_link[link]:
                for sentence in composer.sentences:
                    years = re.findall("([12]?[0-9]{3})( BC| B.C.| BC.)?",
                                       sentence)  # TODO: Fix this damn regex (also: don't forget dates 0-1000)
                    years = [int(y) for y, bc in years if len(bc) == 0 and int(y) <= datetime.datetime.now().year]
                    if years:
                        locations = loc_parser.get_countries(sentence)
                        if locations:
                            x[link].append(TemporospatialEntry(years, list(locations), sentence, composer.name))
                    pbar.update(1)
            pbar.close()

        return x, list(loc_parser.countries_found), loc_parser.country_codes

    @staticmethod
    def filter_outliers(temporospatial_data: dict, order: list) -> dict:  # TODO: Make it work using the order list
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
