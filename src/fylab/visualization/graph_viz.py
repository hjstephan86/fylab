"""
fylab.visualization.graph_viz
==============================
Visualisierung von Finanzgraphen (Transaktionen, MST, Monte Carlo).

Verwendet ausschließlich numpy + matplotlib – kein networkx.
Kreislayout: Knoten gleichmäßig auf Einheitskreis, Start oben.
"""

from __future__ import annotations

import math

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from fylab.algorithms.mst import MSTResult
from fylab.algorithms.subgraph_finance import FraudDetectionResult


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def _circular_layout(
    nodes: list[str], radius: float = 1.0
) -> dict[str, tuple[float, float]]:
    """Kreisförmiges Layout – deterministisch, Start oben (−π/2)."""
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: (0.0, 0.0)}
    offset = -math.pi / 2
    return {
        node: (
            radius * math.cos(2 * math.pi * i / n + offset),
            radius * math.sin(2 * math.pi * i / n + offset),
        )
        for i, node in enumerate(nodes)
    }


# ---------------------------------------------------------------------------
# Zeichenhilfsfunktionen
# ---------------------------------------------------------------------------

def _draw_node(
    ax, x: float, y: float, label: str, color: str, radius: float = 0.07
) -> None:
    circle = plt.Circle((x, y), radius, color=color, zorder=3)
    ax.add_patch(circle)
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=8, color="white", fontweight="bold",
        zorder=4,
    )


def _draw_directed_edge(
    ax,
    pos_u: tuple[float, float],
    pos_v: tuple[float, float],
    lw: float = 1.5,
    color: str = "#555555",
    rad: float = 0.15,
) -> None:
    """Gerichteter gebogener Pfeil von pos_u nach pos_v."""
    ax.annotate(
        "",
        xy=pos_v,
        xytext=pos_u,
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=7,
            shrinkB=7,
        ),
        zorder=2,
    )


def _draw_edge_label(
    ax,
    pos_u: tuple[float, float],
    pos_v: tuple[float, float],
    label: str,
    rad: float = 0.15,
) -> None:
    x1, y1 = pos_u
    x2, y2 = pos_v
    mx = (x1 + x2) / 2 + rad * (y2 - y1) * 0.4
    my = (y1 + y2) / 2 - rad * (x2 - x1) * 0.4
    ax.text(
        mx, my, label,
        fontsize=7, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7, edgecolor="none"),
        zorder=5,
    )


# ---------------------------------------------------------------------------
# Öffentliche Plot-Funktionen
# ---------------------------------------------------------------------------

def plot_transaction_graph(
    graph: dict[str, dict[str, float]],
    fraud_results: list[FraudDetectionResult] | None = None,
    title: str = "Transaktionsgraph",
) -> Figure:
    """
    Visualisiert das Transaktionsnetzwerk.

    Parameters
    ----------
    graph : Adjazenzdict {sender: {empfänger: betrag}}
    fraud_results : Betrugsergebnisse zur Knoten-Hervorhebung (optional)
    """
    # Alle Knoten: Sender explizit als Keys, Empfänger implizit aus Werten
    nodes: list[str] = list(graph.keys())
    for targets in graph.values():
        for tgt in targets:
            if tgt not in nodes:
                nodes.append(tgt)

    pos = _circular_layout(nodes)

    detected_nodes: set[str] = set()
    if fraud_results:
        for r in fraud_results:
            if r.detected and r.mapping:
                detected_nodes.update(r.mapping.keys())

    fig, ax = plt.subplots(figsize=(8, 8))

    all_weights = [w for targets in graph.values() for w in targets.values()]
    max_w = max(all_weights) if all_weights else 1.0

    # Kanten
    for src, targets in graph.items():
        for dst, weight in targets.items():
            if src not in pos or dst not in pos:  # pragma: no cover
                continue  # pragma: no cover
            lw = 1.0 + 3.0 * weight / max_w
            _draw_directed_edge(ax, pos[src], pos[dst], lw=lw)
            _draw_edge_label(ax, pos[src], pos[dst], f"{weight:.0f}€")

    # Knoten (über Kanten)
    for node in nodes:
        x, y = pos[node]
        color = "#e74c3c" if node in detected_nodes else "#3498db"
        _draw_node(ax, x, y, node, color)

    legend_handles = [
        mpatches.Patch(color="#3498db", label="normal"),
        mpatches.Patch(color="#e74c3c", label="Betrugsmuster"),
    ]
    ax.legend(handles=legend_handles, loc="upper right")
    ax.set_title(title)
    ax.set_aspect("equal")
    pad = 0.3
    ax.set_xlim(-1.0 - pad, 1.0 + pad)
    ax.set_ylim(-1.0 - pad, 1.0 + pad)
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_portfolio_mst(mst_result: MSTResult, title: str = "Portfolio-MST") -> Figure:
    """Visualisiert den MST des Portfolios mit Cluster-Färbung."""
    nodes = mst_result.nodes
    edges = mst_result.edges
    pos = _circular_layout(nodes)

    palette = plt.cm.Set2.colors  # type: ignore[attr-defined]
    node_color_map: dict[str, tuple] = {}
    for ci, cluster in enumerate(mst_result.clusters):
        for node in cluster:
            node_color_map[node] = palette[ci % len(palette)]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Kanten (ungerichtet)
    for u, v, w in edges:
        if u not in pos or v not in pos:  # pragma: no cover
            continue  # pragma: no cover
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color="#888888", linewidth=2, zorder=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(
            mx, my, f"{w:.2f}",
            fontsize=7, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8, edgecolor="none"),
            zorder=2,
        )

    # Knoten
    node_r = 0.07
    for node in nodes:
        if node not in pos:
            continue
        x, y = pos[node]
        color = node_color_map.get(node, (0.7, 0.7, 0.7, 1.0))
        circle = plt.Circle((x, y), node_r, color=color, zorder=3)
        ax.add_patch(circle)
        ax.text(
            x, y + node_r + 0.04, node,
            ha="center", va="bottom",
            fontsize=8, fontweight="bold",
            zorder=4,
        )

    ax.set_title(f"{title}  (Gesamtgewicht: {mst_result.total_weight:.3f})")
    ax.set_aspect("equal")
    pad = 0.3
    ax.set_xlim(-1.0 - pad, 1.0 + pad)
    ax.set_ylim(-1.0 - pad, 1.0 + pad)
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_risk_monte_carlo(
    simulations: np.ndarray,
    title: str = "Monte-Carlo-Simulation",
) -> Figure:
    """Visualisiert Monte-Carlo-Pfade des Portfolios."""
    fig, ax = plt.subplots(figsize=(10, 8))
    n_sim, n_days = simulations.shape
    days = np.arange(n_days)

    for i in range(min(200, n_sim)):
        ax.plot(days, simulations[i], alpha=0.05, color="#3498db", linewidth=0.5)

    q05 = np.percentile(simulations, 5, axis=0)
    q50 = np.percentile(simulations, 50, axis=0)
    q95 = np.percentile(simulations, 95, axis=0)

    ax.plot(days, q50, color="#e74c3c", linewidth=2, label="Median")
    ax.fill_between(days, q05, q95, alpha=0.2, color="#e74c3c", label="5%–95%-Bereich")

    ax.set_xlabel("Handelstage")
    ax.set_ylabel("Portfoliowert (€)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
