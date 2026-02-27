import csv
from typing import List

from graph_creation.domain.graph_creator import Municipality
from graph_creation.application.ports import MunicipalityRepository


class CsvMunicipalityRepository(MunicipalityRepository):
    def __init__(self, path: str):
        self.path = path

    def load_municipalities(self) -> List[Municipality]:
        lst = []
        with open(self.path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                m = Municipality(
                    name=r["municipality"],
                    iso_country=r["iso_country"],
                    iso_region=r["iso_region"],
                    latitude=float(r["latitude_deg"]),
                    longitude=float(r["longitude_deg"]),
                    airports=tuple(r["airports"].split(", ")),
                )
                lst.append(m)
        return lst