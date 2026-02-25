from datetime import datetime, timezone
from typing import List

from graph_creation.domain import GraphCreator, Graph
from graph_creation.application.ports import (
    MunicipalityRepository,
    FlightProvider,
    GraphExporter
)


def utc_day_to_unix(day_start: str, day_interval_number:int=1) -> tuple[int, int]:
    """
    Return start and end date in datetime.strptime

    :day_start should be sent in "%Y-%m-%d" format 
    """
    dt = datetime.strptime(day_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    begin = int(dt.timestamp())
    end = begin + day_interval_number * 24 * 3600 - 1
    return begin, end


class CreateGraphService:
    municipality_repo: MunicipalityRepository
    flight_provider: FlightProvider

    def __init__(
        self,
        municipality_repo: MunicipalityRepository,
        flight_provider: FlightProvider
    ):
        self.municipality_repo = municipality_repo
        self.flight_provider = flight_provider


    def execute_since_the_day(self, day_start: str, day_interval_number:int=1) -> GraphCreator:
        """
        :day_start should be sent in "%Y-%m-%d" format 
        """
        begin, end = utc_day_to_unix(day_start, day_interval_number)
        return self.execute(begin, end)


    def execute(self, begin: int, end: int) -> GraphCreator:
        municipalities = self.municipality_repo.load_municipalities()
        graph = GraphCreator(municipalities=municipalities, begin=begin, end=end)

        for flight in self.flight_provider.load_flights(begin, end):
            graph.add_flight(flight)

        print(f"unknown or non-eu departures: {graph.unknown_or_non_eu_dep}")
        print(f"unknown or non-eu arrivals: {graph.unknown_or_non_eu_arr}")

        return graph.to_graph()


class ExportGraphService:
    output_adapters_lst: List[GraphExporter]

    def __init__(self, output_adapters_lst: List[GraphExporter]):
        self.output_adapters_lst = output_adapters_lst

    def export(self, graph: Graph, file_name: str):
        for adapter in self.output_adapters_lst:
            adapter.export(graph, file_name)