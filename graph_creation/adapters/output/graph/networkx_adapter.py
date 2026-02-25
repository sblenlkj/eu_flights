import networkx as nx
from graph_creation.domain import Graph


def node_weight_to_size_translator(w: int):
    return w


class NetworkXAdapter():

    @staticmethod
    def from_graph(graph: Graph) -> nx.DiGraph:
        nx_graph = nx.DiGraph()

        # Add nodes
        for node in graph.nodes:
            nx_graph.add_node(
                node.id,
                size=node_weight_to_size_translator(node.weight),
                label=node.name,
                iso_country=node.iso_country,
                iso_region=node.iso_region,
                latitude=node.latitude,
                longitude=node.longitude,
                airports=node.airports,
            )

        # Add edges
        for edge in graph.edges:
            nx_graph.add_edge(
                edge.from_id,
                edge.to_id,
                weight=edge.weight,
            )

        return nx_graph