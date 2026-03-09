# message_passing_adapter.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

from graph_creation.domain.graph import Graph, GraphType


@dataclass(frozen=True)
class MessagePassingGraph:
    node_ids: List[str]                 # index -> node_id
    node_index: Dict[str, int]          # node_id -> index
    edge_index: np.ndarray              # shape [2, E], dtype int64
    edge_weight: np.ndarray             # shape [E], dtype float32
    x: Optional[np.ndarray] = None      # node features [N, F] if you build them


class MessagePassingAdapter:
    """
    Converts your domain Graph into a message-passing friendly representation, exactly what GNN frameworks expect
    """

    @staticmethod
    def from_graph(
        graph: Graph,
        *,
        add_self_loops: bool = False,
        dtype_weight=np.float32,
    ) -> MessagePassingGraph:
        if graph.graph_type != GraphType.UNDIRECTED:
            raise ValueError("MessagePassingAdapter requires UNDIRECTED graph")

        node_ids = [n.id for n in graph.nodes]
        node_index = {node_id: i for i, node_id in enumerate(node_ids)}

        src: List[int] = []
        dst: List[int] = []
        w: List[float] = []

        def _add(u: str, v: str, weight: float):
            iu = node_index.get(u)
            iv = node_index.get(v)
            if iu is None or iv is None:
                return
            src.append(iu)
            dst.append(iv)
            w.append(weight)

        for e in graph.edges:
            # this ensures symmetric edges for message passing.
            _add(e.from_id, e.to_id, float(e.weight))
            _add(e.to_id, e.from_id, float(e.weight))

        if add_self_loops:
            for node_id in node_ids:
                _add(node_id, node_id, 1.0)

        edge_index = np.array([src, dst], dtype=np.int64)
        edge_weight = np.array(w, dtype=dtype_weight)

        return MessagePassingGraph(
            node_ids=node_ids,
            node_index=node_index,
            edge_index=edge_index,
            edge_weight=edge_weight,
            x=None,
        )