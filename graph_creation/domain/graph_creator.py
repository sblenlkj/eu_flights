from dataclasses import dataclass, field
from typing import List, Dict

from .models import Municipality, Flight
from .graph import Graph, Node, Edge

@dataclass
class EdgeMunicipalityCreator:
    from_id: str
    to_id: str
    weight: int = 0

    def increment(self, by: int = 1) -> None:
        self.weight += by

@dataclass
class EdgesFromMunicipalityCreator:
    municipality_id: str
    edges: Dict[str, EdgeMunicipalityCreator] = field(default_factory=dict)

    def increment(self, to_id: str) -> None:
        if to_id not in self.edges:
            self.edges[to_id] = EdgeMunicipalityCreator(
                from_id=self.municipality_id,
                to_id=to_id,
                weight=0,
            )
        self.edges[to_id].increment()

    def __len__(self):
        return len(self.edges)


@dataclass
class MunicipalityNodeCreator:
    municipality: Municipality
    edges: EdgesFromMunicipalityCreator
    weight: int = 0  # total outgoing weight

    def increment_edge(self, to_id: str):
        self.weight += 1
        self.edges.increment(to_id)


class GraphCreator:
    def __init__(self, municipalities: List[Municipality], begin: int | None = None, end: int | None = None):
        # begin/end define the timeframe (unix timestamps) for which the graph was created
        self.nodes: Dict[str, MunicipalityNodeCreator] = {}
        self.used_nodes: set[str] = set()
        self.airport_index: Dict[str, MunicipalityNodeCreator] = {}

        self.unknown_or_non_eu_dep = 0
        self.unknown_or_non_eu_arr = 0
        self.begin = begin
        self.end = end

        for m in municipalities:
            node = MunicipalityNodeCreator(
                municipality=m,
                edges=EdgesFromMunicipalityCreator(m.id),
            )
            self.nodes[m.id] = node

            for airport in m.airports:
                self.airport_index[airport] = node

    def add_flight(self, flight: Flight):
        src = self.airport_index.get(flight.dep_icao)
        if src is None:
            self.unknown_or_non_eu_dep += 1
            return

        dst = self.airport_index.get(flight.arr_icao)
        if dst is None:
            self.unknown_or_non_eu_arr += 1
            return
        
        self.used_nodes.add(src.municipality.id)
        self.used_nodes.add(dst.municipality.id)

        src.increment_edge(dst.municipality.id)

    def to_graph(self) -> Graph:
        nodes: list[Node] = []
        edges: list[Edge] = []

        # build edges (and you can also build used_nodes here, but we already do it in add_flight)
        for node in self.nodes.values():
            for edge in node.edges.edges.values():
                if edge.weight > 0:
                    edges.append(
                        Edge(
                            from_id=edge.from_id,
                            to_id=edge.to_id,
                            weight=edge.weight,
                        )
                    )

        # build nodes: include both sources and pure-destinations
        for node_id in self.used_nodes:
            node = self.nodes[node_id]
            m = node.municipality
            nodes.append(
                Node(
                    id=m.id,
                    name=m.name,
                    iso_country=m.iso_country,
                    iso_region=m.iso_region,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    airports=list(m.airports),
                    weight=node.weight,  # outgoing total; incoming-only nodes will be 0, and that's OK
                )
            )

        return Graph(
            nodes=nodes,
            edges=edges,
            unknown_or_non_eu_dep=self.unknown_or_non_eu_dep,
            unknown_or_non_eu_arr=self.unknown_or_non_eu_arr,
            begin=self.begin,
            end=self.end,
        )