from typing import *
import csv
import re


class LocationParser:
    def __init__(self):
        with open("countries.txt", "r") as file:
            lines = [line.strip() for line in file.readlines()]
            self.countries_regex = r"(" + "|".join(lines) + ")[ .,\\-!?$]"

        cities_population = {}
        self.country_codes = {}
        self.cities_lut = {}
        with open("worldcities.csv", "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar="\"")
            headers = reader.__next__()
            for row in reader:
                if row[4] not in self.country_codes:
                    self.country_codes[row[4]] = row[5].lower()
                population = -1 if not row[9] else int(float(row[9]))

                if 0 <= population < 50000:
                    continue

                if not row[0] in self.cities_lut or\
                      (row[0] in cities_population and population > cities_population[row[0]]):
                    self.cities_lut[row[0]] = row[4]
                    self.cities_lut[row[1]] = row[4]
                    cities_population[row[0]] = population

        del cities_population
        self.countries_found = set()

    def get_countries(self, sentence: str) -> List[str]:
        found = set()

        for country in re.findall(self.countries_regex, sentence):
            found.add(country)

        for w in range(1, 4):
            for i in range(len(sentence.split(" ")) - (w - 1)):
                name = " ".join(sentence.split(" ")[i:i+w])
                if name in self.cities_lut:
                    found.add(self.cities_lut[name])

        self.countries_found = self.countries_found.union(found)

        return list(found)
