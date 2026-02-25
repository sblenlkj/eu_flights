from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Node:
    id: str
    name: str
    iso_country: str
    iso_region: str
    latitude: float
    longitude: float
    airports: List[str]
    weight: int


@dataclass(frozen=True)
class Edge:
    from_id: str
    to_id: str
    weight: int


@dataclass(frozen=True)
class Graph:
    nodes: List[Node]
    edges: List[Edge]
    unknown_or_non_eu_dep: int
    unknown_or_non_eu_arr: int
    begin: str | None = None
    end: str | None = None


    def __repr__(self):
        return (f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
                f"unknown_or_non_eu_dep={self.unknown_or_non_eu_dep}, "
                f"unknown_or_non_eu_arr={self.unknown_or_non_eu_arr}, "
                f"begin={self.begin}, end={self.end})")