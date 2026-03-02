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
                size=node_weight_to_size_translator(node.out_flights_number),
                label=node.name,
                iso_country=node.iso_country,
                iso_region=node.iso_region,
                latitude=node.latitude,
                longitude=node.longitude,
                airports=node.airports,
                in_flights_number=node.in_flights_number,
                out_flights_number=node.out_flights_number,
                nut3_code=node.nut3_code,
            )

        # Add edges
        for edge in graph.edges:
            nx_graph.add_edge(
                edge.from_id,
                edge.to_id,
                weight=edge.weight,
                distance=edge.distance,
            )

        # record global graph attributes (countries list is recent addition)
        nx_graph.graph["countries"] = graph.countries

        return nx_graph
