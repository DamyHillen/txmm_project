from LocationParser import LocationParser
from data_types import *
from tqdm import tqdm
import numpy as np
import datetime
import logging
import copy
import re
import os

if os.path.isfile("./logs/processor.log"):
    os.remove("./logs/processor.log")

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/processor.log')
file_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(file_handler)
logger.propagate = False


class Processor:
    def preprocess(self, composers_per_link: dict) -> dict:
        result: Dict[str, List[Composer]] = {
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

        x: Dict[str, List[TemporospatialEntry]] = {link: [] for link in composers_per_link}

        for link in x:
            pbar = tqdm(total=sum([len(composer.sentences) for composer in composers_per_link[link]]),
                        desc=f"Filtering years and locations for {link}")
            logger.info(f"Filtering years and locations for \'{link}\'")
            for composer in composers_per_link[link]:
                for sentence in composer.sentences:
                    years = re.findall("([12]?[0-9]{3})( BC| B.C.| BC.)?", sentence)
                    years = [int(y) for y, bc in years if len(bc) == 0 and int(y) <= datetime.datetime.now().year]
                    if years:
                        locations = loc_parser.get_countries(sentence)
                        if locations:
                            x[link].append(TemporospatialEntry(years, list(locations), sentence, composer.name))
                    pbar.update(1)
            pbar.close()

        return x, list(loc_parser.countries_found), loc_parser.country_codes

    @staticmethod
    def filter_outliers(temporospatial_data: dict, order: list) -> dict:
        x = copy.deepcopy(temporospatial_data)

        for _, era, (start, end), _ in order:
            entries: List[TemporospatialEntry] = x[era]

            # Get new start and end year, adding some buffer to the boundaries
            buffer = int((end - start)/4)
            start -= buffer
            end += buffer

            # Filter years too far outside predefined time period
            to_remove: List[int] = []
            for i, entry in enumerate(entries):
                if entry.filter_years(start, end) == 0:
                    to_remove.append(i)

            for idx in reversed(to_remove):
                entries.pop(idx)

        return x
