from dataclasses import dataclass, field
from typing import List, Dict

from .models import Municipality, Flight
from .graph import Graph, Node, Edge
from graph_creation.utils import calculate_distance

MIN_DISTANCE = 150

@dataclass
class EdgeMunicipalityCreator:
    from_id: str
    to_id: str
    weight: int = 0
    distance: float = 0
    # internal map (icao,callsign) -> count
    flights: Dict[tuple[str,str], int] = field(default_factory=dict)

    def increment(self, by: int = 1) -> None:
        self.weight += by

    def add_flight(self, icao: str, callsign: str) -> None:
        key = (icao, callsign)
        self.flights[key] = self.flights.get(key, 0) + 1

@dataclass
class EdgesFromMunicipalityCreator:
    municipality_id: str
    edges: Dict[str, EdgeMunicipalityCreator] = field(default_factory=dict)

    def increment(self, to_id: str, flight_icao: str, callsign: str, distance: float) -> None:
        if to_id not in self.edges:
            self.edges[to_id] = EdgeMunicipalityCreator(
                from_id=self.municipality_id,
                to_id=to_id,
                distance=distance,
                weight=0,
            )
        self.edges[to_id].increment()
        self.edges[to_id].add_flight(flight_icao, callsign)

    def __len__(self):
        return len(self.edges)


@dataclass
class MunicipalityNodeCreator:
    municipality: Municipality
    edges: EdgesFromMunicipalityCreator
    out_flights_number: int = 0  # total outgoing flights

    def increment_edge(self, to_id: str, flight_icao: str, callsign: str, distance: float):
        self.out_flights_number += 1
        self.edges.increment(to_id, flight_icao, callsign, distance)


class GraphCreator:
    """Builds a flight graph incrementally from municipality and flight data.

    The resulting :class:`Graph` object has its ``countries`` attribute set to the
    list of ISO country codes corresponding to nodes that actually participate
    in at least one non‑loop flight.  Internally ``countries`` is a set that is
    updated as flights are added; ``to_graph`` converts it to a sorted list.
    """

    def __init__(self, municipalities: List[Municipality], begin: int | None = None, end: int | None = None):
        # begin/end define the timeframe (unix timestamps) for which the graph was created
        self.nodes: Dict[str, MunicipalityNodeCreator] = {}
        self.used_nodes: set[str] = set()
        self.airport_index: Dict[str, MunicipalityNodeCreator] = {}

        # keep track of which ISO country codes are represented by *used* nodes
        # (nodes that actually participate in flights).  we populate this set
        # while adding flights, then pass the sorted list to the final Graph.
        self.countries: set[str] = set()

        self.unknown_or_non_eu_dep = 0
        self.unknown_or_non_eu_arr = 0
        self.begin = begin
        self.end = end
        self.flights_number = 0
        self.loops = 0
        self.not_enough_distance = 0

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
        
        if src == dst:
            # ignore self loops (flights within the same municipality)
            self.loops += 1
            return
        
        distance = calculate_distance(
            src.municipality.latitude,
            src.municipality.longitude,
            dst.municipality.latitude,
            dst.municipality.longitude,
        )

        if distance < MIN_DISTANCE:
            self.not_enough_distance += 1
            return 

        src.municipality.airports[flight.dep_icao] = True
        dst.municipality.airports[flight.arr_icao] = True

        self.used_nodes.add(src.municipality.id)
        self.used_nodes.add(dst.municipality.id)
        # update country set for all municipalities that are actually used
        self.countries.add(src.municipality.iso_country)
        self.countries.add(dst.municipality.iso_country)

        src.increment_edge(dst.municipality.id, flight.icao, flight.callsign, distance)
        self.flights_number += 1

    def to_graph(self) -> Graph:
        nodes: list[Node] = []
        edges: list[Edge] = []

        # build edges (and you can also build used_nodes here, but we already do it in add_flight)
        for node in self.nodes.values():
            for edge in node.edges.edges.values():
                if edge.weight > 0:
                    # convert internal flights dict -> list of FlightNumber
                    flights_list = []
                    from graph_creation.domain.graph import FlightInEdge, FlightNumber
                    for (icao, callsign), cnt in edge.flights.items():
                        flights_list.append(
                            FlightNumber(
                                flight=FlightInEdge(icao=icao, callsign=callsign),
                                count=cnt,
                            )
                        )
                    
                    edges.append(
                        Edge(
                            from_id=edge.from_id,
                            to_id=edge.to_id,
                            weight=edge.weight,
                            flights=flights_list,
                            distance=edge.distance,
                        )
                    )

        # build nodes: include both sources and pure-destinations
        # compute incoming flights per node
        incoming_counts: Dict[str, int] = {}
        for e in edges:
            incoming_counts[e.to_id] = incoming_counts.get(e.to_id, 0) + e.weight

        for node_id in self.used_nodes:
            node = self.nodes[node_id]
            m = node.municipality
            out_num = node.out_flights_number
            in_num = incoming_counts.get(m.id, 0)
            nodes.append(
                Node(
                    id=m.id,
                    name=m.name,
                    iso_country=m.iso_country,
                    iso_region=m.iso_region,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    airports=[k for k, v in m.airports.items() if v],
                    out_flights_number=out_num,
                    in_flights_number=in_num,
                    nut3_code=None,
                )
            )
        total_flights = self.flights_number

        # convert set -> list; sort for determinism (tests rely on order)
        countries_list = list(sorted(self.countries))

        print(f"Graph created with {len(nodes)} nodes and {len(edges)} edges, flights: {total_flights}")
        return Graph(
            nodes=nodes,
            edges=edges,
            unknown_or_non_eu_dep=self.unknown_or_non_eu_dep,
            unknown_or_non_eu_arr=self.unknown_or_non_eu_arr,
            countries=countries_list,
            begin=self.begin,
            end=self.end,
            nodes_number=len(nodes),
            edges_number=len(edges),
            flights_number=total_flights,
            loops_number=self.loops,
        )
