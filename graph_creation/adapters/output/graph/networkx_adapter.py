import networkx as nx
from graph_creation.domain.graph import Graph, GraphType


class NetworkXAdapter:
    """
    Adapter for converting the custom UNDIRECTED Graph class
    into a NetworkX graph suitable for network analysis.

    Main use cases:
    - assortativity
    - node similarity
    - community detection
    - visualization
    """

    @staticmethod
    def from_graph(graph: Graph) -> nx.Graph:
        """
        Convert custom Graph -> networkx.Graph.

        Requirements:
        - only UNDIRECTED graphs are supported
        - node ids must be unique
        - multiple edges between the same pair are collapsed by NetworkX
          into a single weighted edge (standard nx.Graph behavior)
        """
        if graph.graph_type != GraphType.UNDIRECTED:
            raise ValueError("NetworkXAdapter only supports UNDIRECTED graphs")

        G = nx.Graph()

        # ---- graph-level metadata ----
        G.graph["graph_type"] = str(graph.graph_type)
        G.graph["countries"] = list(graph.countries) if graph.countries is not None else []
        G.graph["begin"] = getattr(graph, "begin", None)
        G.graph["end"] = getattr(graph, "end", None)
        G.graph["n_nodes_original"] = len(graph.nodes)
        G.graph["n_edges_original"] = len(graph.edges)

        # ---- nodes ----
        seen_node_ids = set()

        for node in graph.nodes:
            if node.id in seen_node_ids:
                raise ValueError(f"Duplicate node id detected: {node.id}")
            seen_node_ids.add(node.id)

            traffic = getattr(node, "traffic", 0) or 0
            airports = getattr(node, "airports", None)
            iso_country = getattr(node, "iso_country", None)
            iso_region = getattr(node, "iso_region", None)
            latitude = getattr(node, "latitude", None)
            longitude = getattr(node, "longitude", None)
            nuts3_code = getattr(node, "nut3_code", None)
            node_type = getattr(node, "node_type", None)

            G.add_node(
                node.id,
                # display / id fields
                label=getattr(node, "name", node.id),
                name=getattr(node, "name", node.id),

                # geographic attributes
                iso_country=iso_country,
                iso_region=iso_region,
                latitude=latitude,
                longitude=longitude,

                # airport / graph attributes
                airports=airports,
                traffic=traffic,
                size=traffic,          # convenient alias for plotting
                node_type=node_type,   # useful for assortativity by category
                nuts3_code=nuts3_code, # note: use consistent spelling everywhere
            )

        # ---- edges ----
        for edge in graph.edges:
            u = edge.from_id
            v = edge.to_id

            if u not in G or v not in G:
                raise ValueError(
                    f"Edge ({u}, {v}) refers to a node missing from graph.nodes"
                )

            weight = getattr(edge, "weight", 1) or 1
            distance = getattr(edge, "distance", None)

            G.add_edge(
                u,
                v,
                weight=weight,
                distance=distance,
            )

        # ---- derived node features ----
        degree_dict = dict(G.degree())
        weighted_degree_dict = dict(G.degree(weight="weight"))

        nx.set_node_attributes(G, degree_dict, "degree")
        nx.set_node_attributes(G, weighted_degree_dict, "weighted_degree")

        return G