from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class FlightInEdge:
    icao: str
    callsign: str


@dataclass(frozen=True)
class FlightNumber:
    flight: FlightInEdge
    count: int


@dataclass(frozen=True)
class Node:
    id: str
    name: str
    iso_country: str
    iso_region: str
    latitude: float
    longitude: float
    airports: List[str]
    out_flights_number: int
    in_flights_number: int
    nut3_code: Optional[str] = None


@dataclass(frozen=True)
class Edge:
    from_id: str
    to_id: str
    weight: int
    flights: List[FlightNumber]
    distance: float  # in kilometers


@dataclass(frozen=True)
class Graph:
    nodes: List[Node]
    edges: List[Edge]
    unknown_or_non_eu_dep: int
    unknown_or_non_eu_arr: int
    begin: str | None = None
    end: str | None = None
    nodes_number: int = 0
    edges_number: int = 0
    flights_number: int = 0
    loops_number: int = 0


    def __repr__(self):
        return (f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
                f"unknown_or_non_eu_dep={self.unknown_or_non_eu_dep}, "
                f"unknown_or_non_eu_arr={self.unknown_or_non_eu_arr}, "
                f"begin={self.begin}, end={self.end})")
    
    def __add__(self, other: "Graph") -> "Graph":
        """Merge two Graphs into a new Graph.

        Nodes are merged by `id` (airports lists are unioned, in/out flights summed).
        Edges are merged by `(from_id, to_id)`; weights and flight counts are summed.
        Flight occurrences are aggregated by `(icao, callsign)`.
        Distances are combined as a weighted average by edge weight when possible.
        Summary counters are summed and timeframe spans are combined.
        """
        # Merge nodes
        nodes_map: dict[str, Node] = {}
        for n in (self.nodes or []) + (other.nodes or []):
            if n.id not in nodes_map:
                nodes_map[n.id] = n
            else:
                existing = nodes_map[n.id]
                # combine airports unique-preserving order
                combined_airports = list(dict.fromkeys(existing.airports + n.airports))
                combined_out = existing.out_flights_number + n.out_flights_number
                combined_in = existing.in_flights_number + n.in_flights_number
                nut3 = existing.nut3_code or n.nut3_code
                # prefer existing metadata values (name, iso, coords)
                nodes_map[n.id] = Node(
                    id=existing.id,
                    name=existing.name or n.name,
                    iso_country=existing.iso_country or n.iso_country,
                    iso_region=existing.iso_region or n.iso_region,
                    latitude=existing.latitude or n.latitude,
                    longitude=existing.longitude or n.longitude,
                    airports=combined_airports,
                    out_flights_number=combined_out,
                    in_flights_number=combined_in,
                    nut3_code=nut3,
                )

        merged_nodes = list(nodes_map.values())

        # Merge edges
        from collections import defaultdict

        edges_map: dict[tuple[str, str], dict] = {}

        def add_edge_record(e: Edge):
            key = (e.from_id, e.to_id)
            if key not in edges_map:
                # convert flights list to dict
                flights_agg: dict[tuple[str, str], int] = {}
                for fn in e.flights:
                    flights_agg[(fn.flight.icao, fn.flight.callsign)] = flights_agg.get((fn.flight.icao, fn.flight.callsign), 0) + fn.count
                edges_map[key] = {
                    "weight": e.weight,
                    "flights": flights_agg,
                    "distance_sum": e.distance * e.weight if e.weight else 0.0,
                    "weight_sum": e.weight,
                }
            else:
                rec = edges_map[key]
                rec["weight"] += e.weight
                for fn in e.flights:
                    rec["flights"][(fn.flight.icao, fn.flight.callsign)] = rec["flights"].get((fn.flight.icao, fn.flight.callsign), 0) + fn.count
                rec["distance_sum"] += e.distance * e.weight if e.weight else 0.0
                rec["weight_sum"] += e.weight

        for e in (self.edges or []) + (other.edges or []):
            add_edge_record(e)

        merged_edges: list[Edge] = []
        for (from_id, to_id), rec in edges_map.items():
            # build FlightNumber list
            flights_list = []
            for (icao, callsign), cnt in rec["flights"].items():
                flights_list.append(FlightNumber(flight=FlightInEdge(icao=icao, callsign=callsign), count=cnt))

            # compute average distance if weights exist
            distance = (rec["distance_sum"] / rec["weight_sum"]) if rec["weight_sum"] else 0.0

            merged_edges.append(
                Edge(
                    from_id=from_id,
                    to_id=to_id,
                    weight=rec["weight"],
                    flights=flights_list,
                    distance=distance,
                )
            )

        # Combine summary metrics
        merged_unknown_dep = (self.unknown_or_non_eu_dep or 0) + (other.unknown_or_non_eu_dep or 0)
        merged_unknown_arr = (self.unknown_or_non_eu_arr or 0) + (other.unknown_or_non_eu_arr or 0)
        merged_flights = (self.flights_number or 0) + (other.flights_number or 0)
        merged_loops = (self.loops_number or 0) + (other.loops_number or 0)

        # timeframe: take min begin and max end if present
        begins = [b for b in (self.begin, other.begin) if b is not None]
        ends = [e for e in (self.end, other.end) if e is not None]
        merged_begin = min(begins) if begins else None
        merged_end = max(ends) if ends else None

        merged_graph = Graph(
            nodes=merged_nodes,
            edges=merged_edges,
            unknown_or_non_eu_dep=merged_unknown_dep,
            unknown_or_non_eu_arr=merged_unknown_arr,
            begin=merged_begin,
            end=merged_end,
            nodes_number=len(merged_nodes),
            edges_number=len(merged_edges),
            flights_number=merged_flights,
            loops_number=merged_loops,
        )

        return merged_graph