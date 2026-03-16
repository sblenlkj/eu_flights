from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Municipality:
    name: str
    iso_country: str
    iso_region: str
    latitude: float
    longitude: float
    airports: Dict[str, bool] = field(default_factory=dict)
    id: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'id', f"{self.name}, {self.iso_country}")


@dataclass(frozen=True)
class Flight:
    icao: str
    callsign: str
    dep_icao: str
    arr_icao: str


# placeholder domain models for future enrichment
@dataclass(frozen=True)
class FlightType:
    icao_type: str
    description: str = ""


@dataclass(frozen=True)
class Company:
    name: str
    code: str = ""