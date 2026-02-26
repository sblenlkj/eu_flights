import json
from graph_creation.domain.graph import Graph, Node, Edge


class GraphJsonLoader:

    def load(self, path: str) -> Graph:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        nodes = [Node(**n) for n in data.get("nodes", [])]
        edges = []
        # manually build edges to convert nested flight records
        from graph_creation.domain.graph import FlightInEdge, FlightNumber
        for e in data.get("edges", []):
            flights_list = []
            for fn in e.get("flights", []):
                flight_info = fn.get("flight", {})
                flights_list.append(
                    FlightNumber(
                        flight=FlightInEdge(**flight_info),
                        count=fn.get("count", 0),
                    )
                )
            edges.append(
                Edge(
                    from_id=e.get("from_id"),
                    to_id=e.get("to_id"),
                    weight=e.get("weight", 0),
                    flights=flights_list,
                    distance=e.get("distance", 0.0),
                )
            )

        return Graph(
            nodes=nodes,
            edges=edges,
            unknown_or_non_eu_dep=data.get("unknown_or_non_eu_dep", 0),
            unknown_or_non_eu_arr=data.get("unknown_or_non_eu_arr", 0),
            begin=data.get("begin"),
            end=data.get("end"),
            nodes_number=data.get("nodes_number", len(nodes)),
            edges_number=data.get("edges_number", len(edges)),
            flights_number=data.get("flights_number", 0),
            loops_number=data.get("loops_number", 0),
        )
