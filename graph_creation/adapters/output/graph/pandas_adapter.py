import pandas as pd
from typing import List
from collections import defaultdict

from graph_creation.domain.graph import Graph, GraphType

class GraphPandasAdapter:
    def __init__(self, graph: Graph):
        self.graph = graph

    def nodes_to_df(self) -> pd.DataFrame:
        """Return a DataFrame where each row represents a node.

        All node attributes are included except the list of airports; instead
        a column ``airports_count`` gives the number of airports.
        """
        nodes_edges_count_dct = defaultdict(int)
        for e in self.graph.edges:
            nodes_edges_count_dct[e.from_id] += 1
            nodes_edges_count_dct[e.to_id] += 1


        records = []
        for n in self.graph.nodes:
            rec = {
                "id": n.id,
                "name": n.name,
                "iso_country": n.iso_country,
                "iso_region": n.iso_region,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "airports": ", ".join(n.airports),
                "airports_count": len(n.airports),
                "edges_count": nodes_edges_count_dct[n.id]
            }

            if n.nut3_code is not None:
                rec["nut3_code"] = n.nut3_code
            
            if n.node_type is not None:
                rec["node_type"] = n.node_type

            if self.graph.graph_type == GraphType.DIRECTED:
                rec["node_degree"] = (n.out_flights_number or 0) + (n.in_flights_number or 0)
                rec["out_flights_number"] = n.out_flights_number
                rec["in_flights_number"] = n.in_flights_number

            else:
                rec["node_degree"] = n.traffic or 0

            records.append(rec)
        return pd.DataFrame(records)

    def edges_to_df(self, with_embeddings: bool = False) -> pd.DataFrame:
        """Return a DataFrame with one row per edge.

        If `with_embeddings=True` and `graph.edge_embedding_columns` is defined,
        embedding values are expanded into separate columns.
        """
        records = []

        from_col, to_col = "from_id", "to_id"
        if self.graph.graph_type == GraphType.UNDIRECTED:
            from_col, to_col = "id1", "id2"

        embedding_columns = self.graph.edge_embedding_columns or []

        for e in self.graph.edges:
            rec = {
                from_col: e.from_id,
                to_col: e.to_id,
                "weight": e.weight,
                "distance": e.distance,
            }

            if with_embeddings:
                if embedding_columns:
                    values = list(e.embeddings) if e.embeddings is not None else []
                    if len(values) < len(embedding_columns):
                        values = values + [None] * (len(embedding_columns) - len(values))
                    elif len(values) > len(embedding_columns):
                        values = values[:len(embedding_columns)]

                    rec.update(dict(zip(embedding_columns, values)))
                elif e.embeddings is not None:
                    for i, val in enumerate(e.embeddings):
                        rec[f"embedding_{i}"] = val

            records.append(rec)

        return pd.DataFrame(records)

    def flights_to_df(self) -> pd.DataFrame:
        """Return aggregated flight counts across all edges.

        Columns are ``icao``, ``callsign`` and ``count``.
        """
        agg: dict[tuple[str, str], int] = {}
        for e in self.graph.edges:
            for fn in e.flights:
                key = (fn.flight.icao, fn.flight.callsign)
                agg[key] = agg.get(key, 0) + fn.count

        rows: List[dict] = []
        for (icao, callsign), cnt in agg.items():
            rows.append({"icao": icao, "callsign": callsign, "count": cnt})
        return pd.DataFrame(rows)
    
    def edges_to_df_standard(self, with_embeddings: bool = False) -> pd.DataFrame:
        """
        Same as edges_to_df, but always returns columns:
        source, target, weight, distance, ...
        """
        df = self.edges_to_df(with_embeddings=with_embeddings).copy()

        rename_map = {}
        if "from_id" in df.columns:
            rename_map["from_id"] = "source"
        if "to_id" in df.columns:
            rename_map["to_id"] = "target"
        if "id1" in df.columns:
            rename_map["id1"] = "source"
        if "id2" in df.columns:
            rename_map["id2"] = "target"

        return df.rename(columns=rename_map)
