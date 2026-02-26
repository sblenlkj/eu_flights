import folium
from graph_creation.domain import Graph
from graph_creation.application.ports import GraphExporter
from graph_creation.utils import build_output_path


def node_weight_to_size_translator(w: int):
    return w


class FoliumMapExporter(GraphExporter):
    def __init__(self, output_dir: str = "data/graphs_json_html"):
        self.output_dir = output_dir

    def export(self, graph: Graph, file_name: str) -> None:
        output_path = build_output_path(file_name, default_ext='.html', postfix='_map', out_dir=self.output_dir)

        fmap = folium.Map(zoom_start=5)

        # Add nodes
        for node in graph.nodes:
            popup_text = f"{node.name} (out:{node.out_flights_number}, in:{node.in_flights_number})"
            if node.nut3_code:
                popup_text += f"\nNUT3: {node.nut3_code}"
            folium.CircleMarker(
                location=(node.latitude, node.longitude),
                radius=2 + node_weight_to_size_translator(node.out_flights_number),
                popup=popup_text,
                fill=True,
            ).add_to(fmap)

        # Optional: add edges as lines
        node_index = {n.id: n for n in graph.nodes}

        for edge in graph.edges:
            src = node_index.get(edge.from_id)
            dst = node_index.get(edge.to_id)

            if not src or not dst:
                continue

            folium.PolyLine(
                locations=[
                    (src.latitude, src.longitude),
                    (dst.latitude, dst.longitude),
                ],
                weight=max(1, edge.weight / 10),
                opacity=0.6,
            ).add_to(fmap)

        fmap.save(output_path)