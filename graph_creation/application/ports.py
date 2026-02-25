from abc import ABC, abstractmethod
from typing import Iterable

from graph_creation.domain import Municipality, Flight, Graph


class MunicipalityRepository(ABC):
    @abstractmethod
    def load_municipalities(self) -> list[Municipality]:
        ...


class FlightProvider(ABC):
    @abstractmethod
    def load_flights(self, begin: int, end: int) -> Iterable[Flight]:
        ...


class GraphExporter(ABC):
    @abstractmethod
    def export(self, graph: Graph, file_name: str) -> None:
        ...