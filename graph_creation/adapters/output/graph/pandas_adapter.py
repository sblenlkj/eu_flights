import pandas as pd
from typing import List

from graph_creation.domain.graph import Graph


class GraphPandasAdapter:
    def __init__(self, graph: Graph):
        self.graph = graph

    def nodes_to_df(self) -> pd.DataFrame:
        """Return a DataFrame where each row represents a node.

        All node attributes are included except the list of airports; instead
        a column ``airports_count`` gives the number of airports.
        """
        records = []
        for n in self.graph.nodes:
            rec = {
                "id": n.id,
                "name": n.name,
                "iso_country": n.iso_country,
                "iso_region": n.iso_region,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "airports_count": len(n.airports),
                "out_flights_number": n.out_flights_number,
                "in_flights_number": n.in_flights_number,
                "nut3_code": n.nut3_code,
            }
            records.append(rec)
        return pd.DataFrame(records)

    def edges_to_df(self, with_embedings: bool = False) -> pd.DataFrame:
        """Return a DataFrame with one row per edge.

        We omit the ``flights`` list for now.  If the graph has
        ``edge_embedding_columns`` defined and the edges have
        ``embeddings`` vectors, those values are added as separate columns.
        """
        records = []
        for e in self.graph.edges:
            rec = {
                "from_id": e.from_id,
                "to_id": e.to_id,
                "weight": e.weight,
                "distance": e.distance,
            }
            if with_embedings and self.graph.edge_embedding_columns is not None and e.embeddings is not None:
                for name, val in zip(self.graph.edge_embedding_columns, e.embeddings):
                    rec[name] = val
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
