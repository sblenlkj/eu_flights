import json
from datetime import datetime, timezone
from graph_creation.domain import Graph
from graph_creation.utils import build_output_path


class GraphJsonExporter:
    def __init__(self, output_dir: str = "data/graphs_json_html"):
        self.output_dir = output_dir

    def export(self, graph: Graph, file_name: str) -> None:
        path = build_output_path(file_name, default_ext='.json', postfix=None, out_dir=self.output_dir)

        def _ts_to_human(ts: int | None) -> str | None:
            if ts is None:
                return None
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # prepare serializable node and edge dictionaries
        nodes_list = [n.__dict__ for n in graph.nodes]
        edges_list = []
        for e in graph.edges:
            # convert flights to simple dicts.  embeddings (if present) are
            # intentionally omitted from the exported payload; they are only
            # used for in‑memory analytics / CSV adapters.
            flights_serial = []
            for fn in e.flights:
                flights_serial.append({
                    "flight": fn.flight.__dict__,
                    "count": fn.count,
                })
            edges_list.append({
                "from_id": e.from_id,
                "to_id": e.to_id,
                "weight": e.weight,
                "flights": flights_serial,
                "distance": e.distance,
                "embeddings": e.embeddings
            })

        payload = {
            "nodes": nodes_list,
            "edges": edges_list,
            "graph_type": graph.graph_type,
            "unknown_or_non_eu_dep": graph.unknown_or_non_eu_dep,
            "unknown_or_non_eu_arr": graph.unknown_or_non_eu_arr,
            "edge_embedding_columns": graph.edge_embedding_columns,
            "countries": graph.countries,
            "begin": _ts_to_human(graph.begin) if isinstance(graph.begin, int) else graph.begin,
            "end": _ts_to_human(graph.end) if isinstance(graph.end, int) else graph.end,
            "nodes_number": graph.nodes_number,
            "edges_number": graph.edges_number,
            "flights_number": graph.flights_number,
            "loops_number": graph.loops_number,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

