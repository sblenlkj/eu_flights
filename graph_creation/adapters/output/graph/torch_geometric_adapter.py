import torch
from torch_geometric.data import Data

from graph_creation.domain.graph import Graph, GraphType


class PyTorchGeometricAdapter:
    """
    Converts domain Graph into torch_geometric.data.Data

    Only UNDIRECTED graphs are supported.
    """

    @staticmethod
    def from_graph(
        graph: Graph,
        *,
        add_self_loops: bool = False,
        dtype_weight=torch.float32,
    ) -> Data:

        if graph.graph_type != GraphType.UNDIRECTED:
            raise ValueError(
                "PyTorchGeometricAdapter requires UNDIRECTED graph"
            )

        node_ids = [n.id for n in graph.nodes]
        node_index = {nid: i for i, nid in enumerate(node_ids)}

        src = []
        dst = []
        weights = []

        for e in graph.edges:
            i = node_index.get(e.from_id)
            j = node_index.get(e.to_id)

            if i is None or j is None:
                continue

            # undirected → add both directions
            src.append(i)
            dst.append(j)
            weights.append(float(e.weight))

            src.append(j)
            dst.append(i)
            weights.append(float(e.weight))

        if add_self_loops:
            for i in range(len(node_ids)):
                src.append(i)
                dst.append(i)
                weights.append(1.0)

        edge_index = torch.tensor([src, dst], dtype=torch.long)
        edge_weight = torch.tensor(weights, dtype=dtype_weight)

        # node feature example: traffic
        x = torch.tensor(
            [[n.traffic] for n in graph.nodes],
            dtype=torch.float32,
        )

        data = Data(
            x=x,
            edge_index=edge_index,
            edge_weight=edge_weight,
        )

        data.node_ids = node_ids
        data.countries = graph.countries
        data.begin = graph.begin
        data.end = graph.end

        return data