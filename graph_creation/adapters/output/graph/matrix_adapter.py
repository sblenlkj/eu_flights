from typing import Dict, List, Tuple
import numpy as np
from graph_creation.domain import Graph


class ConnectivityMatrixAdapter:
    """
    Converts your domain Graph into a weighted adjacency matrix.

    Output:
      - A: np.ndarray [N, N] (float)
      - node_ids: list[str] (index -> node_id)
      - index: dict[str, int] (node_id -> index)
    """

    @staticmethod
    def from_graph(
        graph: Graph,
        *,
        dtype=float,
        include_self_loops: bool = False,
        normalize: str | None = None,  # None | "row" | "sym"
    ) -> Tuple[np.ndarray, List[str], Dict[str, int]]:
        # stable ordering for reproducibility
        node_ids = [n.id for n in graph.nodes]
        index = {node_id: i for i, node_id in enumerate(node_ids)}

        n = len(node_ids)
        A = np.zeros((n, n), dtype=dtype)

        # fill adjacency (directed)
        for e in graph.edges:
            i = index.get(e.from_id)
            j = index.get(e.to_id)
            if i is None or j is None:
                # graph should be consistent, but be defensive
                continue
            A[i, j] += e.weight

        if include_self_loops:
            np.fill_diagonal(A, 1.0)

        if normalize == "row":
            # D^{-1} A
            row_sum = A.sum(axis=1, keepdims=True)
            row_sum[row_sum == 0] = 1.0
            A = A / row_sum

        elif normalize == "sym":
            # D^{-1/2} A D^{-1/2}
            deg = A.sum(axis=1)
            deg[deg == 0] = 1.0
            inv_sqrt = 1.0 / np.sqrt(deg)
            A = (A * inv_sqrt[:, None]) * inv_sqrt[None, :]

        return A, node_ids, index