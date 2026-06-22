"""
fylab.visualization.portfolio_chart
=====================================
Tortendiagramm (Asset-Allocation) und Effizienzgrenze.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from fylab.core.portfolio import Portfolio
from fylab.analysis.portfolio_opt import EfficientFrontierResult


def plot_asset_allocation(portfolio: Portfolio) -> Figure:
    """Tortendiagramm der Asset-Allokation."""
    alloc = portfolio.asset_class_allocation()
    labels = list(alloc.keys())
    sizes = list(alloc.values())

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        startangle=140, pctdistance=0.8,
    )
    ax.set_title(f"Asset-Allokation: {portfolio.name}")
    fig.tight_layout()
    return fig


def plot_efficient_frontier(
    result: EfficientFrontierResult,
    symbols: list[str] | None = None,
    asset_vols: np.ndarray | None = None,
    asset_rets: np.ndarray | None = None,
) -> Figure:
    """Markowitz-Effizienzgrenze."""
    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(
        result.volatilities * 100,
        result.returns * 100,
        c=result.sharpe_ratios,
        cmap="viridis",
        s=15,
        zorder=2,
    )
    plt.colorbar(sc, ax=ax, label="Sharpe-Ratio")

    # Optimales Portfolio markieren
    ax.scatter(
        result.optimal_volatility * 100,
        result.optimal_return * 100,
        color="red", marker="*", s=200, zorder=3,
        label=f"Optimum (Sharpe={result.optimal_sharpe:.2f})",
    )

    # Einzelne Assets einzeichnen
    if asset_vols is not None and asset_rets is not None and symbols is not None:
        ax.scatter(asset_vols * 100, asset_rets * 100, color="black", s=40, zorder=4)
        for sym, v, r in zip(symbols, asset_vols, asset_rets):
            ax.annotate(sym, (v * 100, r * 100), textcoords="offset points",
                        xytext=(5, 3), fontsize=8)

    ax.set_xlabel("Volatilität (% p.a.)")
    ax.set_ylabel("Erwartete Rendite (% p.a.)")
    ax.set_title("Markowitz-Effizienzgrenze")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
