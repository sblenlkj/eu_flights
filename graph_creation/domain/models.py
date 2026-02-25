from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class Municipality:
    name: str
    iso_country: str
    iso_region: str
    latitude: float
    longitude: float
    airports: Tuple[str, ...]
    id: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'id', f"{self.name}, {self.iso_country}")


@dataclass(frozen=True)
class Flight:
    flight_icao: str
    dep_icao: str
    arr_icao: str