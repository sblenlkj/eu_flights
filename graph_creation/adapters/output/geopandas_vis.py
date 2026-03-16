import math
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Point, LineString
from matplotlib.lines import Line2D
from adjustText import adjust_text

from graph_creation.adapters.output.graph.pandas_adapter import GraphPandasAdapter
from graph_creation.domain.graph import Graph


WORLD_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"


def graph_to_pandas(graph: Graph, with_embeddings: bool = False):
    """
    Use AFTER your existing cleaning code.
    """
    adapter = GraphPandasAdapter(graph)
    nodes_df = adapter.nodes_to_df()
    edges_df = adapter.edges_to_df_standard(with_embeddings=with_embeddings)
    return nodes_df, edges_df


def _build_color_map(values, cmap_name="tab20"):
    values = pd.Series(values).fillna("unknown").astype(str)
    uniq = list(values.unique())

    cmap = plt.get_cmap(cmap_name, max(len(uniq), 1))
    color_map = {val: cmap(i) for i, val in enumerate(uniq)}
    return color_map


def visualize_graph_geopandas(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    countries: list[str] | None = None,
    color_by: str = "node_type",          # e.g. "node_type" or "iso_country"
    size_by: str = "node_degree",         # e.g. "node_degree", "airports_count", "edges_count"
    label_top_n: int = 15,
    label_by: str = "node_degree",
    figsize: tuple[int, int] = (20, 12),
    europe_xlim: tuple[float, float] = (-15, 45),
    europe_ylim: tuple[float, float] = (34, 72),
    edge_alpha: float = 0.08,
    edge_linewidth_scale: float = 0.35,
    node_size_min: float = 20,
    node_size_max: float = 350,
    show_legend: bool = True,
    title: str | None = None,
):
    """
    Plot graph on Europe map using nodes_df + edges_df.

    Typical usage:
        nodes_df, edges_df = graph_to_pandas(clean_graph)
        visualize_graph_geopandas(
            nodes_df, edges_df,
            countries=["FR", "GB"],
            color_by="iso_country"
        )
    """
    nodes_df = nodes_df.copy()
    edges_df = edges_df.copy()

    # 1) Optional country filter
    if countries is not None:
        countries_set = set(countries)
        nodes_df = nodes_df[nodes_df["iso_country"].isin(countries_set)].copy()

    valid_ids = set(nodes_df["id"])
    edges_df = edges_df[
        edges_df["source"].isin(valid_ids) & edges_df["target"].isin(valid_ids)
    ].copy()

    # 2) Drop rows without coords
    nodes_df = nodes_df.dropna(subset=["latitude", "longitude"]).copy()
    valid_ids = set(nodes_df["id"])
    edges_df = edges_df[
        edges_df["source"].isin(valid_ids) & edges_df["target"].isin(valid_ids)
    ].copy()

    # 3) Build points GeoDataFrame
    nodes_gdf = gpd.GeoDataFrame(
        nodes_df,
        geometry=gpd.points_from_xy(nodes_df["longitude"], nodes_df["latitude"]),
        crs="EPSG:4326"
    )

    # 4) Merge coords into edges and build LineStrings
    coords = nodes_df[["id", "longitude", "latitude"]].copy()

    edges_geo = (
        edges_df
        .merge(coords.rename(columns={
            "id": "source",
            "longitude": "source_lon",
            "latitude": "source_lat",
        }), on="source", how="left")
        .merge(coords.rename(columns={
            "id": "target",
            "longitude": "target_lon",
            "latitude": "target_lat",
        }), on="target", how="left")
    )

    edges_geo = edges_geo.dropna(
        subset=["source_lon", "source_lat", "target_lon", "target_lat"]
    ).copy()

    edges_geo["geometry"] = edges_geo.apply(
        lambda r: LineString([
            (r["source_lon"], r["source_lat"]),
            (r["target_lon"], r["target_lat"]),
        ]),
        axis=1,
    )

    edges_gdf = gpd.GeoDataFrame(edges_geo, geometry="geometry", crs="EPSG:4326")

    # 5) Background map
    world = gpd.read_file(WORLD_URL)
    europe = world.cx[europe_xlim[0]:europe_xlim[1], europe_ylim[0]:europe_ylim[1]]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#eef7fb")

    europe.plot(ax=ax, color="#f5f5f5", edgecolor="#cfcfcf", linewidth=0.6)

    # 6) Edges
    if len(edges_gdf) > 0:
        if "weight" in edges_gdf.columns and edges_gdf["weight"].notna().any():
            lw = np.log1p(edges_gdf["weight"].fillna(1)) * edge_linewidth_scale
            lw = np.clip(lw, 0.15, 2.0)
        else:
            lw = 0.3

        edges_gdf.plot(
            ax=ax,
            color="gray",
            alpha=edge_alpha,
            linewidth=lw,
            zorder=1,
        )

    # 7) Colors
    if color_by not in nodes_gdf.columns:
        raise ValueError(f"Column '{color_by}' not found in nodes_df")

    nodes_gdf[color_by] = nodes_gdf[color_by].fillna("unknown").astype(str)
    color_map = _build_color_map(nodes_gdf[color_by], cmap_name="tab20")
    nodes_gdf["_color"] = nodes_gdf[color_by].map(color_map)

    # 8) Node sizes
    if size_by not in nodes_gdf.columns:
        sizes = np.full(len(nodes_gdf), 50.0)
    else:
        vals = pd.to_numeric(nodes_gdf[size_by], errors="coerce").fillna(0.0)
        if vals.max() == vals.min():
            sizes = np.full(len(vals), (node_size_min + node_size_max) / 2)
        else:
            scaled = (vals - vals.min()) / (vals.max() - vals.min())
            sizes = node_size_min + scaled * (node_size_max - node_size_min)

    # 9) Nodes
    nodes_gdf.plot(
        ax=ax,
        color=nodes_gdf["_color"],
        markersize=sizes,
        edgecolor="black",
        linewidth=0.25,
        alpha=0.9,
        zorder=2,
    )

    # 10) Labels for top hubs
    texts = []
    if label_by in nodes_gdf.columns and label_top_n > 0:
        label_df = (
            nodes_gdf.sort_values(label_by, ascending=False)
            .head(label_top_n)
        )
        for _, row in label_df.iterrows():
            label = str(row["id"]).split(",")[0]
            texts.append(
                ax.text(
                    row.geometry.x,
                    row.geometry.y,
                    label,
                    fontsize=9,
                    weight="bold",
                    zorder=3,
                )
            )

        if texts:
            adjust_text(
                texts,
                ax=ax,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.4),
            )

    # 11) Legend
    if show_legend:
        uniq_values = list(nodes_gdf[color_by].dropna().astype(str).unique())
        if len(uniq_values) <= 20:
            handles = [
                Line2D(
                    [0], [0],
                    marker="o",
                    color="w",
                    markerfacecolor=color_map[val],
                    markeredgecolor="black",
                    markeredgewidth=0.3,
                    markersize=8,
                    label=val
                )
                for val in uniq_values
            ]
            ax.legend(
                handles=handles,
                title=color_by,
                loc="lower left",
                frameon=True,
                fontsize=9,
                title_fontsize=10,
                ncol=1 if len(uniq_values) <= 10 else 2,
            )

    ax.set_xlim(*europe_xlim)
    ax.set_ylim(*europe_ylim)
    ax.axis("off")

    if title is None:
        title = f"EU flights graph colored by {color_by}"

    ax.set_title(title, fontsize=18, pad=16)
    plt.tight_layout()
    plt.show()

    return fig, ax, nodes_gdf, edges_gdf