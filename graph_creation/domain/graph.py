from dataclasses import dataclass
from typing import List, Optional, Dict, Union, Set, Self, Tuple
from enum import Enum
from collections import defaultdict, Counter

class GraphType(str, Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


@dataclass()
class FlightInEdge:
    icao: str
    callsign: str
    model: Optional[str] = None


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
    matching_values: List[str]


@dataclass()
class Node:
    id: str
    name: str
    iso_country: str
    iso_region: str
    latitude: float
    longitude: float
    airports: List[str]

    out_flights_number: Optional[int] = None
    in_flights_number: Optional[int] = None

    traffic: Optional[int] = None
    nut3_code: Optional[str] = None
    node_type: Optional[str] = None


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

    graph_type: GraphType = GraphType.DIRECTED
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
        if self.graph_type == GraphType.DIRECTED:
            return (
                f"Graph(type=DIRECTED, nodes={self.nodes_number}, edges={self.edges_number}, "
                f"flights={self.flights_number}, countries={len(self.countries)}, "
                f"begin={self.begin}, end={self.end})"
            )

        return (
            f"Graph(type=UNDIRECTED, nodes={self.nodes_number}, edges={self.edges_number}, "
            f"flights={self.flights_number}, countries={len(self.countries)}, "
            f"begin={self.begin}, end={self.end})"
        )
    

    def __add__(self, other: "Graph") -> "Graph":
        """Merge two Graphs into a new Graph.

        Nodes are merged by `id` (airports lists are unioned, in/out flights summed).
        Edges are merged by `(from_id, to_id)`; weights and flight counts are summed.
        Flight occurrences are aggregated by `(icao, callsign)`.
        Distances are combined as a weighted average by edge weight when possible.
        Summary counters are summed and timeframe spans are combined.
        """

        if self.graph_type != GraphType.DIRECTED or other.graph_type != GraphType.DIRECTED:
            raise ValueError(
                "__add__ only supported for DIRECTED graphs. "
                "Convert graphs before merging or merge raw directed graphs."
            )

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
                    nut3_code=existing.nut3_code,
                    node_type=existing.node_type
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
    
    def _validate_node_semantics(self):
        if self.graph_type == GraphType.DIRECTED:
            for n in self.nodes:
                if n.traffic is not None:
                    raise ValueError("Directed nodes must not have traffic")

        else:
            for n in self.nodes:
                if n.in_flights_number is not None or n.out_flights_number is not None:
                    raise ValueError("Undirected nodes must not have in/out counters")

    # --- additional helpers -------------------------------------------------
    def copy(self) -> "Graph":
        """Return a shallow-deep hybrid copy: new container objects, copied records."""
        self._validate_node_semantics()
    
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
            graph_type=self.graph_type,
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

            if self.graph_type == GraphType.DIRECTED:
                # create a new Node instance to avoid mutating potential external refs
                out_num = n.out_flights_number - out_adjust.get(n.id, 0)
                in_num = n.in_flights_number - in_adjust.get(n.id, 0)
                out_num = max(out_num, 0)
                in_num = max(in_num, 0)

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
                        traffic=None,
                        nut3_code=n.nut3_code,
                        node_type=n.node_type
                    )
                )

            else:  # UNDIRECTED
                traffic = n.traffic - (
                    out_adjust.get(n.id, 0) + in_adjust.get(n.id, 0)
                )
                traffic = max(traffic, 0)

                new_nodes.append(
                    Node(
                        id=n.id,
                        name=n.name,
                        iso_country=n.iso_country,
                        iso_region=n.iso_region,
                        latitude=n.latitude,
                        longitude=n.longitude,
                        airports=list(n.airports),
                        out_flights_number=None,
                        in_flights_number=None,
                        traffic=traffic,
                        nut3_code=n.nut3_code,
                        node_type=n.node_type
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
        to_remove = {
            n.id
            for n in (self.nodes or [])
            if n.iso_country in country_codes
        }

        if not to_remove:
            print('No nodes for the countries found. Nothing is deleted!')
            return self
        return self.drop_nodes(to_remove)


    def create_edge_embeddings(
        self,
        callsign_embeddings: List[Embedding],
        model_embeddings: List[Embedding],
        assign_to_edges: bool = False,
        normalize: bool = True,
        add_size_features: bool = True,
        add_coverage_features: bool = True,
        keep_raw_counts: bool = False,
    ) -> List[List[float]]:
        """
        Create semantic edge feature vectors from flights.

        Layout:
        - optional raw counts for company groups
        - optional raw counts for aircraft groups
        - normalized shares for company groups
        - normalized shares for aircraft groups
        - optional coverage features
        - optional size features

        Notes:
        - callsign group is matched by first 3 chars of callsign
        - model group is matched by exact `flight.model`
        - company shares are normalized by matched company flights only
        - aircraft shares are normalized by matched aircraft flights only
        - size features are kept separate from semantic shares
        """
        result: List[List[float]] = []

        callsign_names = [emb.name for emb in callsign_embeddings]
        model_names = [emb.name for emb in model_embeddings]

        callsign_lookup: Dict[str, int] = {}
        for idx, emb in enumerate(callsign_embeddings):
            for value in emb.matching_values:
                callsign_lookup[value] = idx

        model_lookup: Dict[str, int] = {}
        for idx, emb in enumerate(model_embeddings):
            for value in emb.matching_values:
                model_lookup[value] = idx

        column_names: List[str] = []

        if keep_raw_counts:
            column_names.extend([f"cnt_{name}" for name in callsign_names])
            column_names.extend([f"cnt_{name}" for name in model_names])

        column_names.extend([f"pct_{name}" for name in callsign_names])
        column_names.extend([f"pct_{name}" for name in model_names])

        if add_coverage_features:
            column_names.extend([
                "operator_coverage",
                "aircraft_coverage",
            ])

        if add_size_features:
            column_names.extend([
                "log_total_flights",
                "log_unique_callsigns",
            ])

        for e in (self.edges or []):
            callsign_counts = [0] * len(callsign_embeddings)
            model_counts = [0] * len(model_embeddings)

            total_flights = 0
            matched_callsign_flights = 0
            matched_model_flights = 0
            unique_callsigns: Set[str] = set()

            for fn in e.flights:
                cnt = fn.count
                total_flights += cnt

                callsign_raw = fn.flight.callsign or ""
                callsign_prefix = callsign_raw[:3]
                if callsign_raw:
                    unique_callsigns.add(callsign_raw)

                callsign_idx = callsign_lookup.get(callsign_prefix)
                if callsign_idx is not None:
                    callsign_counts[callsign_idx] += cnt
                    matched_callsign_flights += cnt

                model_raw = fn.flight.model
                if model_raw is not None:
                    model_idx = model_lookup.get(model_raw)
                    if model_idx is not None:
                        model_counts[model_idx] += cnt
                        matched_model_flights += cnt

            row: List[float] = []

            if keep_raw_counts:
                row.extend(float(x) for x in callsign_counts)
                row.extend(float(x) for x in model_counts)

            if normalize:
                if matched_callsign_flights > 0:
                    row.extend(x / matched_callsign_flights for x in callsign_counts)
                else:
                    row.extend(0.0 for _ in callsign_counts)

                if matched_model_flights > 0:
                    row.extend(x / matched_model_flights for x in model_counts)
                else:
                    row.extend(0.0 for _ in model_counts)
            else:
                row.extend(float(x) for x in callsign_counts)
                row.extend(float(x) for x in model_counts)

            if add_coverage_features:
                if total_flights > 0:
                    row.append(matched_callsign_flights / total_flights)
                    row.append(matched_model_flights / total_flights)
                else:
                    row.append(0.0)
                    row.append(0.0)

            if add_size_features:
                import math
                row.append(math.log1p(total_flights))
                row.append(math.log1p(len(unique_callsigns)))

            result.append(row)

        if assign_to_edges:
            self.edge_embedding_columns = column_names
            for e, vec in zip(self.edges or [], result):
                e.embeddings = vec.copy()

        return result


    def to_undirected(self) -> "Graph":
        """Return a new graph where A→B and B→A edges are merged."""
        self._validate_node_semantics()

        if self.graph_type == GraphType.UNDIRECTED:
            return self.copy()

        edge_map: Dict[Tuple, Dict[str, Union[float, Dict[Tuple, int]]]] = {}

        def edge_key(a, b):
            return (a, b) if a < b else (b, a)

        for e in self.edges:
            key = edge_key(e.from_id, e.to_id)

            if key not in edge_map:
                edge_map[key] = {
                    "distance": e.distance,
                    "flights": defaultdict(int),
                }

            rec = edge_map[key]
            for fn in e.flights:
                k = (fn.flight.icao, fn.flight.callsign)
                rec["flights"][k] = max(fn.count, rec["flights"][k])

        new_edges: List[Edge] = []
        for (id1, id2), rec in edge_map.items():

            flights = [
                FlightNumber(
                    flight=FlightInEdge(icao=icao, callsign=callsign),
                    count=count
                )
                for (icao, callsign), count in rec["flights"].items()
            ]
            weight = sum(fn.count for fn in flights)

            new_edges.append(
                Edge(
                    from_id=id1,
                    to_id=id2,
                    weight=weight,
                    flights=flights,
                    distance=rec["distance"],
                )
            )

        # recompute node counters
        node_map = {n.id: Node(**vars(n)) for n in self.nodes}

        for n in node_map.values():
            n.in_flights_number = None
            n.out_flights_number = None
            n.traffic = 0

        for e in new_edges:
            node_map[e.from_id].traffic += e.weight
            node_map[e.to_id].traffic += e.weight

        new_nodes = list(node_map.values())

        g = Graph(
            nodes=new_nodes,
            edges=new_edges,
            graph_type=GraphType.UNDIRECTED,
            unknown_or_non_eu_dep=self.unknown_or_non_eu_dep,
            unknown_or_non_eu_arr=self.unknown_or_non_eu_arr,
            countries=list(self.countries),
            begin=self.begin,
            end=self.end,
            nodes_number=len(new_nodes),
            edges_number=len(new_edges),
            flights_number=self.flights_number,
            loops_number=self.loops_number,
        )
        g._validate_node_semantics()

        return g
    
    def populate_node_types(self, airport_label_map: dict[str, str]) -> Counter:
        """
        Populate node_type for each node using airport-level labels.

        Rules:
        - 2+ large airports -> 2plus_large_airports
        - exactly 2 large airports and only 2 airports total -> 2_large_airports
        - otherwise if any large airport -> large
        - otherwise if any medium airport -> medium
        - otherwise -> small

        Args:
            airport_label_map:
                Mapping ICAO -> airport size label ('small', 'medium', 'large')
            exceptions:
                Raise an exception when a node contains an airport code missing from airport_label_map or an unsupported label.
        """
        def _assign_node_type_from_airport_labels(airport_labels: list[str]) -> str:
            counts = Counter(airport_labels)
            n_large = counts.get("large_airport", 0) 
            n_medium = counts.get("medium_airport", 0)
            # total = len(airport_labels)

            # if n_large >= 2:
            #     if n_large == 2 and total == 2:
            #         return "2_large_airports"
            #     return "2plus_large_airports"

            if n_large >= 1:
                return "large"

            if n_medium >= 1:
                return "medium"

            return "small"

        for node in self.nodes:
            airport_labels: list[str] = []
            for code in node.airports:
                label = airport_label_map.get(code)

                if label is None:
                    raise ValueError(f"Missing airport label for code={code!r} in node={node.name!r}")
                if label.strip("_airport") not in {"small", "medium", "large"}:
                    raise ValueError(f"Unsupported airport label {label!r} for code={code!r}")

                airport_labels.append(label)


            node.node_type = _assign_node_type_from_airport_labels(airport_labels)

        return Counter([n.node_type for n in self.nodes])
    
    @property
    def node_types(self):
        return Counter([n.node_type for n in self.nodes])
    
    def filter_edges(self, edges_to_keep: List[List[str]]) -> Self:
        """Filter the graph to keep only the specified edges.

        For undirected graphs only. Removes edges not in the provided list,
        removes nodes that are not connected by any remaining edge, and
        recomputes the traffic attribute for remaining nodes.

        Args:
            edges_to_keep: List of Edge objects to retain in the graph.

        Returns:
            Self: The modified graph.
        """
        if self.graph_type != GraphType.UNDIRECTED:
            raise ValueError("filter_edges only supported for undirected graphs")

        # Create a set of edge keys (sorted tuples for undirected comparison)
        keep_keys = set()
        for e in edges_to_keep:
            key = tuple(sorted(e))
            keep_keys.add(key)

        # Filter edges
        new_edges: list[Edge] = []
        for e in self.edges:
            key = (min(e.from_id, e.to_id), max(e.from_id, e.to_id))
            if key in keep_keys:
                new_edges.append(e)

        # Collect node ids present in remaining edges
        node_ids = set()
        for e in new_edges:
            node_ids.add(e.from_id)
            node_ids.add(e.to_id)

        # Filter nodes
        new_nodes = [n for n in self.nodes if n.id in node_ids]

        # Recompute traffic
        traffic = defaultdict(int)
        for e in new_edges:
            traffic[e.from_id] += e.weight
            traffic[e.to_id] += e.weight

        for n in new_nodes:
            n.traffic = traffic.get(n.id, 0)

        # Update graph attributes
        self.nodes = new_nodes
        self.edges = new_edges
        self.nodes_number = len(new_nodes)
        self.edges_number = len(new_edges)
        self.flights_number = sum(e.weight for e in new_edges)
        self.countries = list(set(n.iso_country for n in new_nodes if n.iso_country))

        return self