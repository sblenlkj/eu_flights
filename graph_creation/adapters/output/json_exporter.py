import json
from datetime import datetime, timezone
from graph_creation.domain import Graph
from graph_creation.utils import build_output_path


class GraphJsonExporter:
    def export(self, graph: Graph, file_name: str) -> None:
        path = build_output_path(file_name, default_ext='.json', postfix=None, out_dir='data')

        def _ts_to_human(ts: int | None) -> str | None:
            if ts is None:
                return None
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        payload = {
            "nodes": [n.__dict__ for n in graph.nodes],
            "edges": [e.__dict__ for e in graph.edges],
            "unknown_or_non_eu_dep": graph.unknown_or_non_eu_dep,
            "unknown_or_non_eu_arr": graph.unknown_or_non_eu_arr,
            "begin": _ts_to_human(graph.begin) if isinstance(graph.begin, int) else graph.begin,
            "end": _ts_to_human(graph.end) if isinstance(graph.end, int) else graph.end,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

