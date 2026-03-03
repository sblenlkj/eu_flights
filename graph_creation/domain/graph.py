from dataclasses import dataclass
from typing import List, Optional, Dict, Union, Set, Self


@dataclass(frozen=True)
class FlightInEdge:
    icao: str
    callsign: str


@dataclass(frozen=True)
class FlightNumber:
    flight: FlightInEdge
    count: int


@dataclass(frozen=True)
class Embedding:
    """Simple holder for an embedding schema used when counting matches.

    The ``embedding`` attribute can be any vector representation (float list).  The
    ``matching_columns`` list contains the raw codes or identifiers that should
    be compared with either flight callsign prefixes or ICAO codes.
    """
    name: str
    matching_columns: List[str]


@dataclass()
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


@dataclass()
class Edge:
    from_id: str
    to_id: str
    weight: int
    flights: List[FlightNumber]
    distance: float  # in kilometers
    # optional embedding vector; not serialized by JSON exporter but used in
    # pandas adapter when present.  Length matches ``graph.edge_embedding_columns``.
    embeddings: Optional[List[int]] = None


@dataclass()
class Graph:
    nodes: List[Node]
    edges: List[Edge]
    unknown_or_non_eu_dep: int
    unknown_or_non_eu_arr: int
    # list of country ISO codes representing countries of the remaining nodes
    countries: List[str]
    # column names associated with ``Edge.embeddings``; if ``None`` no
    # embeddings are attached.
    edge_embedding_columns: Optional[List[str]] = None
    begin: str | None = None
    end: str | None = None
    nodes_number: int = 0
    edges_number: int = 0
    flights_number: int = 0
    loops_number: int = 0


    def __repr__(self):
        return (f"Graph(nodes_number={self.nodes_number}, edges_number={self.edges_number}, "
                f"unknown_or_non_eu_dep={self.unknown_or_non_eu_dep}, "
                f"unknown_or_non_eu_arr={self.unknown_or_non_eu_arr}, "
                f"countries={self.countries}, "
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

        # union country lists, preserving order but deduplicating
        merged_countries = []
        for lst in (self.countries or [], other.countries or []):
            for c in lst:
                if c not in merged_countries:
                    merged_countries.append(c)

        # embeddings cannot be reliably preserved through a merge; drop
        # them and force callers to recompute if desired.
        merged_edge_cols = None
        for e in merged_edges:
            e.embeddings = None

        merged_graph = Graph(
            nodes=merged_nodes,
            edges=merged_edges,
            unknown_or_non_eu_dep=merged_unknown_dep,
            unknown_or_non_eu_arr=merged_unknown_arr,
            countries=merged_countries,
            edge_embedding_columns=merged_edge_cols,
            begin=merged_begin,
            end=merged_end,
            nodes_number=len(merged_nodes),
            edges_number=len(merged_edges),
            flights_number=merged_flights,
            loops_number=merged_loops,
        )

        return merged_graph

    # --- additional helpers -------------------------------------------------
    def copy(self) -> "Graph":
        """Return a shallow-deep hybrid copy: new container objects, copied records."""
        nodes_copy = [Node(**vars(n)) for n in (self.nodes or [])]
        # copy flights inside edges too
        edges_copy = []
        for e in (self.edges or []):
            flights_copy = [FlightNumber(flight=FlightInEdge(**vars(fn.flight)), count=fn.count) for fn in e.flights]
            edges_copy.append(
                Edge(
                    from_id=e.from_id,
                    to_id=e.to_id,
                    weight=e.weight,
                    flights=flights_copy,
                    distance=e.distance,
                    embeddings=list(e.embeddings) if e.embeddings is not None else None,
                )
            )

        # for old version, when countries attribute was None
        if self.countries is not None:
            countries_copy = list(self.countries)
        else:
            print("countries attribute is None")

        # edge columns
        cols_copy = list(self.edge_embedding_columns) if self.edge_embedding_columns is not None else None

        return Graph(
            nodes=nodes_copy,
            edges=edges_copy,
            unknown_or_non_eu_dep=self.unknown_or_non_eu_dep,
            unknown_or_non_eu_arr=self.unknown_or_non_eu_arr,
            countries=countries_copy,
            edge_embedding_columns=cols_copy,
            begin=self.begin,
            end=self.end,
            nodes_number=self.nodes_number,
            edges_number=self.edges_number,
            flights_number=self.flights_number,
            loops_number=self.loops_number,
        )

    def drop_nodes(self, node_ids: Union[List[str], Set[str]]) -> Self:
        """Remove nodes from `country_code` and adjust edge weights / node counters.

        This mutates the graph in-place: nodes from the provided country are
        deleted, any edges touching those nodes are removed, and remaining
        nodes' in/out counters are decremented by the weights of removed edges.
        """
        if isinstance(node_ids, list):
            node_ids = set(node_ids)
        
        out_adjust: dict[str, int] = {}
        in_adjust: dict[str, int] = {}
        removed_flights = 0

        new_edges: list[Edge] = []
        for e in (self.edges or []):
            if e.from_id in node_ids or e.to_id in node_ids:
                removed_flights += e.weight
                # if only one side is removed, decrement the other's counters
                if e.from_id not in node_ids:
                    out_adjust[e.from_id] = out_adjust.get(e.from_id, 0) + e.weight
                
                if e.to_id not in node_ids:
                    in_adjust[e.to_id] = in_adjust.get(e.to_id, 0) + e.weight

                continue
            new_edges.append(e)

        # build new node list applying adjustments
        new_nodes: list[Node] = []
        countries = set()
        for n in (self.nodes or []):
            if n.id in node_ids:
                continue
            
            # create a new Node instance to avoid mutating potential external refs
            out_num = n.out_flights_number - out_adjust.get(n.id, 0)
            in_num = n.in_flights_number - in_adjust.get(n.id, 0)
            if out_num < 0:
                out_num = 0
            if in_num < 0:
                in_num = 0

            new_nodes.append(
                Node(
                    id=n.id,
                    name=n.name,
                    iso_country=n.iso_country,
                    iso_region=n.iso_region,
                    latitude=n.latitude,
                    longitude=n.longitude,
                    airports=list(n.airports),
                    out_flights_number=out_num,
                    in_flights_number=in_num,
                    nut3_code=n.nut3_code,
                )
            )
            countries.add(n.iso_country)

        self.nodes = new_nodes
        self.edges = new_edges
        self.nodes_number = len(new_nodes)
        self.edges_number = len(new_edges)
        self.flights_number = max(0, (self.flights_number or 0) - removed_flights)
        if countries != {None}:
            self.countries = list(countries)
        
        return self


    def drop_countries(self, country_codes: List[str]) -> Self:
        """Helper for drop_nodes methods. 
        It allows to drop nodes from the specific countries
        """
        to_remove = {n.id for n in (self.nodes or []) if n.iso_country in country_codes}
        if not to_remove:
            print('No nodes for the countries found. Nothing is deleted!')
            return self
        return self.drop_nodes(to_remove)


    def create_edge_embeddings(
        self,
        callsign_embeddings: List["Embedding"],
        icao_embeddings: List["Embedding"],
        icao_to_model_dct: Dict[str, str],
        assign_to_edges: bool = False,
    ) -> List[List[int]]:
        """Create count-vectors per edge matching flights against provided embeddings.

        The output list aligns with `self.edges` order. The vector layout is
        [callsign_embeddings..., icao_embeddings...], each value equals the sum
        of `count` for flights matching that embedding's `matching_columns`.

        If ``assign_to_edges`` is ``True`` the resulting vectors are written to
        ``Edge.embeddings`` and the graph's
        ``edge_embedding_columns`` field is populated with the corresponding
        embedding names, allowing downstream code (e.g. pandas adapter) to
        expose them as separate columns.  By default the method is pure and
        returns the matrix only.
        """
        def callsign_cleaning(s: str):
            return s[:3] if s[:3].isalpha() else None

        def icao_cleaning(s: str):
            return s
        
        def check_model(model: str, matching_columns: List[str]):
            for one in matching_columns:
                if one in model:
                    return True
            return False

        result: List[List[int]] = []
        for e in (self.edges or []):
            counts = [0] * (len(callsign_embeddings) + len(icao_embeddings))
            for fn in e.flights:
                # callsign block
                callsign = callsign_cleaning(fn.flight.callsign)
                if callsign is not None:
                    for idx, emb in enumerate(callsign_embeddings):
                        if callsign in emb.matching_columns:
                            counts[idx] += fn.count
                
                # icao block
                icao = icao_cleaning(fn.flight.icao)
                if icao is not None and icao in icao_to_model_dct:
                    model = icao_to_model_dct[icao]
                    offset = len(callsign_embeddings)
                    for idx, emb in enumerate(icao_embeddings):
                        if check_model(model, emb.matching_columns):
                            counts[offset + idx] += fn.count

            result.append(counts)

        if assign_to_edges:
            # attach back to edge objects and remember column names
            names = [emb.name for emb in callsign_embeddings] + [emb.name for emb in icao_embeddings]
            self.edge_embedding_columns = names
            for e, vec in zip(self.edges or [], result):
                e.embeddings = vec.copy()

        return result
