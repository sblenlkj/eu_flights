import networkx as nx
from graph_creation.domain.graph import Graph, GraphType


class NetworkXAdapter:

    @staticmethod
    def from_graph(graph: Graph) -> nx.Graph:

        if graph.graph_type != GraphType.UNDIRECTED:
            raise ValueError("NetworkXAdapter only supports UNDIRECTED graphs")

        nx_graph = nx.Graph()

        for node in graph.nodes:
            nx_graph.add_node(
                node.id,
                size=node.traffic,
                label=node.name,
                iso_country=node.iso_country,
                iso_region=node.iso_region,
                latitude=node.latitude,
                longitude=node.longitude,
                airports=node.airports,
                traffic=node.traffic,
                nut3_code=node.nut3_code,
            )

        for edge in graph.edges:
            nx_graph.add_edge(
                edge.from_id,
                edge.to_id,
                weight=edge.weight,
                distance=edge.distance,
            )

        nx_graph.graph["countries"] = graph.countries

        return nx_graph