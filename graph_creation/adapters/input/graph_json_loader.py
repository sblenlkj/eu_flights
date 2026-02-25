import json
from graph_creation.domain.graph import Graph, Node, Edge


class GraphJsonLoader:

    @staticmethod
    def load(path: str) -> Graph:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        nodes = [Node(**n) for n in data["nodes"]]
        edges = [Edge(**e) for e in data["edges"]]

        return Graph(
            nodes=nodes,
            edges=edges,
            unknown_or_non_eu_dep=data.get("unknown_or_non_eu_dep", 0),
            unknown_or_non_eu_arr=data.get("unknown_or_non_eu_arr", 0),
            begin=data.get("begin"),
            end=data.get("end"),
        )
