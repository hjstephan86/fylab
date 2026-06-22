"""
Generates all figures for MANUAL.md.
Run from repo root: python doc/generate_manual_figures.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import math
from datetime import date
import pathlib

OUT = pathlib.Path(__file__).parent / "figures"
for _sub in ("", "/svg", "/pdf"):
    (OUT / _sub.lstrip("/") if _sub else OUT).mkdir(exist_ok=True)

OUT_SVG = OUT / "svg"
OUT_PDF = OUT / "pdf"


def _save(fig, name: str) -> None:
    """Save figure as PNG (figures/), SVG (figures/svg/) and PDF (figures/pdf/)."""
    kw_vec = dict(bbox_inches="tight", transparent=False)
    fig.savefig(OUT     / f"{name}.png", dpi=150, bbox_inches="tight")
    fig.savefig(OUT_SVG / f"{name}.svg", **kw_vec)
    fig.savefig(OUT_PDF / f"{name}.pdf", **kw_vec)
    print(f"  ✓ {name}  [png / svg / pdf]")

# ─────────────────────────────────────────────────────────────────────────────
# 0.  Style defaults
# ─────────────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 130,
    "figure.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Cashflow Waterfall
# ─────────────────────────────────────────────────────────────────────────────
def fig_cashflow_waterfall():
    monthly_values = {
        "2026-01": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-02": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-03": 3200 - 850 - 400 - 500 - 110 - 35 - 320,  # Kfz-Steuer
        "2026-04": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-05": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-06": 3200 - 850 - 400 - 500 - 110 - 35 + 3000,  # Bonus
        "2026-07": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-08": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-09": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-10": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-11": 3200 - 850 - 400 - 500 - 110 - 35,
        "2026-12": 3200 - 850 - 400 - 500 - 110 - 35,
    }
    months = [f"2026-{m:02d}" for m in range(1, 13)]
    values = np.array([monthly_values.get(m, 0.0) for m in months])
    cumulative = np.cumsum(values)
    month_labels = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]
    ax1.bar(month_labels, values, color=colors, edgecolor="white", linewidth=0.5)
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_ylabel("Netto-Cashflow (€)")
    ax1.set_title("Monatlicher Cashflow – Haushaltsplan 2026", fontsize=13, fontweight="bold")
    ax1.grid(True, axis="y", alpha=0.3)
    for i, (lbl, v) in enumerate(zip(month_labels, values)):
        ax1.text(i, v + (50 if v >= 0 else -80), f"{v:+.0f}", ha="center", va="bottom", fontsize=8)

    ax2.plot(month_labels, cumulative, marker="o", color="#3498db", linewidth=2, label="Kumuliert")
    ax2.fill_between(range(12), cumulative, alpha=0.15, color="#3498db")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Kumulierter Cashflow (€)")
    ax2.set_xlabel("Monat")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    _save(fig, "cashflow_waterfall")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Asset Allocation Pie
# ─────────────────────────────────────────────────────────────────────────────
def fig_asset_allocation():
    alloc = {
        "Aktie":        (5 * 420 + 15 * 185 + 3 * 875),
        "ETF":          (100 * 32 + 80 * 108),
        "Kryptowährung":(0.05 * 65000),
        "Liquidität":   2500,
    }
    total = sum(alloc.values())
    labels = list(alloc.keys())
    sizes = [v / total for v in alloc.values()]
    colors = ["#3498db", "#2ecc71", "#f39c12", "#95a5a6"]

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        startangle=140, pctdistance=0.82, colors=colors,
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax.set_title("Asset-Allokation: Mein Depot", fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "asset_allocation")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Efficient Frontier
# ─────────────────────────────────────────────────────────────────────────────
def fig_efficient_frontier():
    rng = np.random.default_rng(42)
    symbols = ["MSFT", "AAPL", "NVDA", "EWG.DE", "VWRL.L", "BTC"]
    n = len(symbols)
    exp_ret = rng.uniform(0.04, 0.22, n)
    A = rng.standard_normal((n, n))
    cov = A @ A.T / n * 0.04
    vols = np.sqrt(np.diag(cov))

    # Simple efficient frontier via random portfolios
    n_rand = 4000
    rand_w = rng.dirichlet(np.ones(n), n_rand)
    p_vols = np.sqrt(np.einsum("ij,jk,ik->i", rand_w, cov, rand_w))
    p_rets = rand_w @ exp_ret
    p_sharpe = (p_rets - 0.03) / p_vols

    # Optimal (max sharpe)
    opt_idx = np.argmax(p_sharpe)
    opt_v, opt_r, opt_s = p_vols[opt_idx], p_rets[opt_idx], p_sharpe[opt_idx]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    sc = ax.scatter(
        p_vols * 100, p_rets * 100,
        c=p_sharpe, cmap="viridis", s=8, alpha=0.6,
    )
    plt.colorbar(sc, ax=ax, label="Sharpe-Ratio")
    ax.scatter(opt_v * 100, opt_r * 100, color="red", marker="*",
               s=250, zorder=5, label=f"Optimum (Sharpe={opt_s:.2f})")
    ax.scatter(vols * 100, exp_ret * 100, color="black", s=60, zorder=6)
    for sym, v, r in zip(symbols, vols, exp_ret):
        ax.annotate(sym, (v * 100, r * 100), textcoords="offset points",
                    xytext=(6, 3), fontsize=8)
    ax.set_xlabel("Volatilität (% p.a.)", fontsize=11)
    ax.set_ylabel("Erwartete Rendite (% p.a.)", fontsize=11)
    ax.set_title("Markowitz-Effizienzgrenze", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, "efficient_frontier")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Portfolio MST
# ─────────────────────────────────────────────────────────────────────────────
def fig_portfolio_mst():
    symbols = ["MSFT", "AAPL", "NVDA", "EWG.DE", "VWRL.L", "BTC"]
    # Manually crafted correlation matrix with clusters
    corr = np.array([
        [1.00,  0.85,  0.72,  0.30, 0.35,  0.10],
        [0.85,  1.00,  0.68,  0.28, 0.32,  0.08],
        [0.72,  0.68,  1.00,  0.20, 0.25,  0.15],
        [0.30,  0.28,  0.20,  1.00, 0.75, -0.05],
        [0.35,  0.32,  0.25,  0.75, 1.00,  0.02],
        [0.10,  0.08,  0.15, -0.05, 0.02,  1.00],
    ])
    dist = np.sqrt(np.clip(2.0 * (1.0 - corr), 0.0, None))
    n = len(symbols)

    # Kruskal MST
    edges = sorted(
        [(float(dist[i, j]), symbols[i], symbols[j])
         for i in range(n) for j in range(i + 1, n)]
    )
    parent = {s: s for s in symbols}
    rank = {s: 0 for s in symbols}
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry: return False
        if rank[rx] < rank[ry]: rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]: rank[rx] += 1
        return True

    mst_edges = []
    for w, u, v in edges:
        if union(u, v):
            mst_edges.append((u, v, w))
        if len(mst_edges) == n - 1:
            break

    # Circular layout
    offset = -math.pi / 2
    pos = {s: (math.cos(2 * math.pi * i / n + offset),
               math.sin(2 * math.pi * i / n + offset))
           for i, s in enumerate(symbols)}

    # Cluster colors (Tech vs Europe vs Crypto)
    cluster_colors = {"MSFT": "#3498db", "AAPL": "#3498db", "NVDA": "#3498db",
                      "EWG.DE": "#2ecc71", "VWRL.L": "#2ecc71", "BTC": "#f39c12"}

    fig, ax = plt.subplots(figsize=(7, 6))
    for u, v, w in mst_edges:
        x1, y1 = pos[u]; x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color="#888888", linewidth=2, zorder=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, f"{w:.2f}", fontsize=7.5, ha="center",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.85, edgecolor="none"))

    for s, (x, y) in pos.items():
        circle = plt.Circle((x, y), 0.10, color=cluster_colors[s], zorder=3)
        ax.add_patch(circle)
        ax.text(x, y + 0.15, s, ha="center", va="bottom", fontsize=9, fontweight="bold")

    legend_items = [
        mpatches.Patch(color="#3498db", label="US-Tech"),
        mpatches.Patch(color="#2ecc71", label="Europa-ETF"),
        mpatches.Patch(color="#f39c12", label="Krypto"),
    ]
    ax.legend(handles=legend_items, loc="lower right")
    ax.set_title("Portfolio-MST: Diversifikationscluster (Pearson-Distanz)", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
    ax.axis("off")
    fig.tight_layout()
    _save(fig, "portfolio_mst")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Monte-Carlo Simulation
# ─────────────────────────────────────────────────────────────────────────────
def fig_monte_carlo():
    rng = np.random.default_rng(42)
    mu = 0.08 / 252
    sigma = 0.20 / np.sqrt(252)
    n_sim, n_days = 3000, 252
    v0 = 100_000.0

    sims = np.zeros((n_sim, n_days + 1))
    sims[:, 0] = v0
    for t in range(1, n_days + 1):
        r = rng.normal(mu, sigma, n_sim)
        sims[:, t] = sims[:, t - 1] * (1 + r)

    days = np.arange(n_days + 1)
    q05 = np.percentile(sims, 5, axis=0)
    q25 = np.percentile(sims, 25, axis=0)
    q50 = np.percentile(sims, 50, axis=0)
    q75 = np.percentile(sims, 75, axis=0)
    q95 = np.percentile(sims, 95, axis=0)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i in range(min(300, n_sim)):
        ax.plot(days, sims[i], alpha=0.04, color="#3498db", linewidth=0.5)
    ax.fill_between(days, q05, q95, alpha=0.18, color="#e74c3c", label="5%–95%-Band")
    ax.fill_between(days, q25, q75, alpha=0.25, color="#e74c3c", label="25%–75%-Band")
    ax.plot(days, q50, color="#c0392b", linewidth=2.2, label=f"Median (={q50[-1]:,.0f} €)")
    ax.plot(days, q05, color="#e74c3c", linewidth=1.2, linestyle="--", label=f"5%-Quantil (={q05[-1]:,.0f} €)")
    ax.axhline(v0, color="black", linewidth=0.8, linestyle=":", label=f"Startwert ({v0:,.0f} €)")
    ax.set_xlabel("Handelstage", fontsize=11)
    ax.set_ylabel("Portfoliowert (€)", fontsize=11)
    ax.set_title(f"Monte-Carlo-Simulation ({n_sim:,} Pfade, μ=8% p.a., σ=20% p.a.)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    fig.tight_layout()
    _save(fig, "monte_carlo")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Transaction Graph with Fraud
# ─────────────────────────────────────────────────────────────────────────────
def _circ(nodes, radius=1.0):
    n = len(nodes)
    offset = -math.pi / 2
    return {nd: (radius * math.cos(2 * math.pi * i / n + offset),
                 radius * math.sin(2 * math.pi * i / n + offset))
            for i, nd in enumerate(nodes)}


def _arrow(ax, p1, p2, color="#555", lw=1.5, rad=0.18):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                connectionstyle=f"arc3,rad={rad}",
                                shrinkA=9, shrinkB=9))


def fig_transaction_graph():
    nodes = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
    txns = [
        ("Alice", "Bob",   1500), ("Bob",   "Carol",  800), ("Carol", "Alice",  900),
        ("Alice", "Dave",   200), ("Alice", "Eve",    150), ("Alice", "Frank",  300),
        ("Alice", "Grace",  100), ("Dave",  "Heidi",  180), ("Heidi", "Ivan",   160),
        ("Ivan",  "Judy",   140),
    ]
    fraud_nodes = {"Alice", "Bob", "Carol"}  # wash-trading cycle
    pos = _circ(nodes, radius=1.0)

    fig, ax = plt.subplots(figsize=(9, 7))
    max_w = max(w for _, _, w in txns)
    for src, dst, w in txns:
        lw = 0.8 + 3.0 * w / max_w
        color = "#e74c3c" if src in fraud_nodes and dst in fraud_nodes else "#95a5a6"
        _arrow(ax, pos[src], pos[dst], color=color, lw=lw)
        mx = (pos[src][0] + pos[dst][0]) / 2
        my = (pos[src][1] + pos[dst][1]) / 2
        ax.text(mx, my, f"{w}€", fontsize=6.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.08", facecolor="white", alpha=0.75, edgecolor="none"))

    for nd, (x, y) in pos.items():
        color = "#e74c3c" if nd in fraud_nodes else "#3498db"
        circle = plt.Circle((x, y), 0.085, color=color, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, nd[:5], ha="center", va="center",
                fontsize=7.5, color="white", fontweight="bold", zorder=4)

    legend_handles = [
        mpatches.Patch(color="#3498db", label="Normal"),
        mpatches.Patch(color="#e74c3c", label="Wash-Trading erkannt"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", fontsize=9)
    ax.set_title("Transaktionsnetzwerk – Betrugsmuster erkannt (Subgraph-ISO)", fontsize=12, fontweight="bold")
    ax.set_aspect("equal"); ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
    ax.axis("off")
    fig.tight_layout()
    _save(fig, "transaction_graph")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Fraud Pattern Topologies
# ─────────────────────────────────────────────────────────────────────────────
def fig_fraud_patterns():
    fig, axes = plt.subplots(1, 4, figsize=(13, 4))

    def draw_pattern(ax, title, nodes, edges, pos):
        for u, v in edges:
            _arrow(ax, pos[u], pos[v], color="#e74c3c", lw=2, rad=0.2 if len(nodes) == 2 else 0.12)
        for nd, (x, y) in pos.items():
            circle = plt.Circle((x, y), 0.15, color="#e74c3c", zorder=3)
            ax.add_patch(circle)
            ax.text(x, y, nd, ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold", zorder=4)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5)

    # Wash-Trading: A ↔ B
    p1 = {"A": (-0.6, 0), "B": (0.6, 0)}
    draw_pattern(axes[0], "Wash-Trading\nA → B → A",
                 ["A", "B"], [("A", "B"), ("B", "A")], p1)

    # Smurfing star
    p2 = {"S": (0, 0.4), "B1": (-0.9, -0.5), "B2": (-0.3, -0.7), "B3": (0.3, -0.7), "B4": (0.9, -0.5)}
    draw_pattern(axes[1], "Smurfing\nStern-Verteilung",
                 ["S", "B1", "B2", "B3", "B4"],
                 [("S", "B1"), ("S", "B2"), ("S", "B3"), ("S", "B4")], p2)

    # Layering chain
    p3 = {"A": (-1.0, 0), "B": (-0.33, 0), "C": (0.33, 0), "D": (1.0, 0)}
    draw_pattern(axes[2], "Layering\nKettenstruktur",
                 ["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "D")], p3)

    # Circular Flow
    r = 0.7
    p4 = {nd: (r * math.cos(2 * math.pi * i / 3 - math.pi / 2),
               r * math.sin(2 * math.pi * i / 3 - math.pi / 2))
          for i, nd in enumerate(["X", "Y", "Z"])}
    draw_pattern(axes[3], "Circular Flow\nRingstruktur",
                 ["X", "Y", "Z"], [("X", "Y"), ("Y", "Z"), ("Z", "X")], p4)

    fig.suptitle("Referenzgraphen der Betrugsmuster (Adjazenzmatrizen R)", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "fraud_patterns")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Arbitrage: Währungsgraph
# ─────────────────────────────────────────────────────────────────────────────
def fig_arbitrage():
    currencies = ["EUR", "USD", "GBP", "JPY", "CHF"]
    rates = {
        ("EUR", "USD"): 1.085, ("USD", "EUR"): 0.9217,
        ("EUR", "GBP"): 0.857, ("GBP", "EUR"): 1.1669,
        ("EUR", "JPY"): 163.2, ("JPY", "EUR"): 0.00613,
        ("EUR", "CHF"): 0.952, ("CHF", "EUR"): 1.0504,
        ("USD", "GBP"): 0.789, ("GBP", "USD"): 1.267,
        ("USD", "JPY"): 150.4, ("JPY", "USD"): 0.00665,
        ("GBP", "JPY"): 190.6, ("JPY", "GBP"): 0.00525,
        ("USD", "CHF"): 0.899, ("CHF", "USD"): 1.115,
    }
    # Arbitrage-Zyklus: EUR->USD->CHF->EUR = 1.085 * 1.115 * 1.0504 ≈ 1.271 (künstlich)
    arbitrage_path = ["EUR", "USD", "CHF", "EUR"]
    arb_edges = list(zip(arbitrage_path, arbitrage_path[1:]))

    n = len(currencies)
    offset = -math.pi / 2
    pos = {c: (math.cos(2 * math.pi * i / n + offset),
               math.sin(2 * math.pi * i / n + offset))
           for i, c in enumerate(currencies)}

    fig, ax = plt.subplots(figsize=(8, 6))
    arb_set = set(map(tuple, arb_edges))
    for (src, dst), rate in rates.items():
        color = "#e74c3c" if (src, dst) in arb_set else "#bdc3c7"
        lw = 2.5 if (src, dst) in arb_set else 0.8
        _arrow(ax, pos[src], pos[dst], color=color, lw=lw, rad=0.15)
        mx = (pos[src][0] + pos[dst][0]) / 2 + 0.08 * (pos[dst][1] - pos[src][1])
        my = (pos[src][1] + pos[dst][1]) / 2 - 0.08 * (pos[dst][0] - pos[src][0])
        fs = 7 if (src, dst) not in arb_set else 8
        fw = "normal" if (src, dst) not in arb_set else "bold"
        ax.text(mx, my, f"{rate}", fontsize=fs, ha="center", va="center", fontweight=fw,
                color="#c0392b" if (src, dst) in arb_set else "#555",
                bbox=dict(boxstyle="round,pad=0.08", facecolor="white", alpha=0.8, edgecolor="none"))

    for c, (x, y) in pos.items():
        circle = plt.Circle((x, y), 0.10, color="#2c3e50", zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, c, ha="center", va="center", fontsize=9,
                color="white", fontweight="bold", zorder=4)

    factor = 1.085 * 1.115 * 1.0504
    ax.set_title(f"Währungsgraph mit Arbitrage-Zyklus\nEUR→USD→CHF→EUR  (Faktor {factor:.4f}×)",
                 fontsize=12, fontweight="bold")
    legend_handles = [
        mpatches.Patch(color="#bdc3c7", label="Normaler Kurs"),
        mpatches.Patch(color="#e74c3c", label="Arbitrage-Zyklus"),
    ]
    ax.legend(handles=legend_handles, loc="lower right")
    ax.set_aspect("equal"); ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5)
    ax.axis("off")
    fig.tight_layout()
    _save(fig, "arbitrage")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Debt Simplification
# ─────────────────────────────────────────────────────────────────────────────
def fig_debt_simplification():
    debts_before = [
        ("Alice", "Bob",   30), ("Alice", "Carol", 20),
        ("Bob",   "Carol", 10), ("Carol", "Dave",  40),
        ("Dave",  "Alice", 25),
    ]
    persons = ["Alice", "Bob", "Carol", "Dave"]
    net = {p: 0.0 for p in persons}
    for payer, receiver, amt in debts_before:
        net[payer] -= amt
        net[receiver] += amt

    # Greedy simplification
    creditors = sorted([(v, k) for k, v in net.items() if v > 0], reverse=True)
    debtors = sorted([(abs(v), k) for k, v in net.items() if v < 0], reverse=True)
    simplified = []
    ci, di = 0, 0
    c_amounts = [v for v, _ in creditors]
    d_amounts = [v for v, _ in debtors]
    while ci < len(creditors) and di < len(debtors):
        settle = min(c_amounts[ci], d_amounts[di])
        simplified.append((debtors[di][1], creditors[ci][1], settle))
        c_amounts[ci] -= settle
        d_amounts[di] -= settle
        if c_amounts[ci] < 1e-6: ci += 1
        if d_amounts[di] < 1e-6: di += 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    def draw_debts(ax, title, txns, persons):
        pos = _circ(persons)
        for payer, receiver, amt in txns:
            _arrow(ax, pos[payer], pos[receiver], color="#e74c3c", lw=1.5, rad=0.2)
            mx = (pos[payer][0] + pos[receiver][0]) / 2 + 0.12 * (pos[receiver][1] - pos[payer][1])
            my = (pos[payer][1] + pos[receiver][1]) / 2 - 0.12 * (pos[receiver][0] - pos[payer][0])
            ax.text(mx, my, f"{amt:.0f}€", fontsize=9, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.1", facecolor="#fff3f3", alpha=0.9, edgecolor="#e74c3c", lw=0.5))
        for nd, (x, y) in pos.items():
            circle = plt.Circle((x, y), 0.14, color="#2c3e50", zorder=3)
            ax.add_patch(circle)
            ax.text(x, y, nd, ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold", zorder=4)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5)

    draw_debts(ax1, f"Vor Vereinfachung\n({len(debts_before)} Transaktionen)", debts_before, persons)
    draw_debts(ax2, f"Nach Greedy-Vereinfachung\n({len(simplified)} Transaktionen)", simplified, persons)

    fig.suptitle("Schuldenausgleich: Greedy Net-Balance-Reduktion", fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "debt_simplification")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 10.  VaR / CVaR Distribution
# ─────────────────────────────────────────────────────────────────────────────
def fig_var_distribution():
    rng = np.random.default_rng(42)
    mu = 0.08 / 252
    sigma = 0.20 / np.sqrt(252)
    returns = rng.normal(mu, sigma, 2520)

    var_95 = float(-np.percentile(returns, 5))
    var_99 = float(-np.percentile(returns, 1))
    tail_95 = returns[returns <= -var_95]
    cvar_95 = float(-tail_95.mean())

    fig, ax = plt.subplots(figsize=(9, 5))
    n_bins = 60
    counts, bins, patches = ax.hist(returns * 100, bins=n_bins, color="#3498db",
                                    alpha=0.6, edgecolor="white", linewidth=0.5, density=True)

    # Color tail regions
    for patch, left_edge in zip(patches, bins[:-1]):
        if left_edge < -var_99 * 100:
            patch.set_facecolor("#c0392b")
            patch.set_alpha(0.9)
        elif left_edge < -var_95 * 100:
            patch.set_facecolor("#e74c3c")
            patch.set_alpha(0.75)

    ax.axvline(-var_95 * 100, color="#e74c3c", linewidth=2, linestyle="--",
               label=f"VaR(95%) = {var_95:.2%}")
    ax.axvline(-var_99 * 100, color="#c0392b", linewidth=2, linestyle="-.",
               label=f"VaR(99%) = {var_99:.2%}")
    ax.axvline(-cvar_95 * 100, color="#8e44ad", linewidth=2, linestyle=":",
               label=f"CVaR(95%) = {cvar_95:.2%}")

    ax.set_xlabel("Tägliche Rendite (%)", fontsize=11)
    ax.set_ylabel("Dichte", fontsize=11)
    ax.set_title("Renditeverteilung: Value-at-Risk und CVaR (Expected Shortfall)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add annotation
    ax.annotate("Verlust-Tail\n(5% schlechteste Tage)",
                xy=(-var_95 * 100 - 0.1, 0.5),
                xytext=(-var_95 * 100 - 1.8, 3.5),
                arrowprops=dict(arrowstyle="->", color="#e74c3c"),
                fontsize=9, color="#e74c3c")

    fig.tight_layout()
    _save(fig, "var_distribution")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 11.  Subgraph Algorithm Overview
# ─────────────────────────────────────────────────────────────────────────────
def fig_subgraph_overview():
    """Visualizes the subgraph algorithm pipeline."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

    titles = [
        "Referenzgraph R\n(Betrugsmuster: Wash-Trading)",
        "Transaktionsgraph G\n(echtes Netzwerk)",
        "Ergebnis: R ⊆ G\n(Muster erkannt!)",
    ]
    # R: 2-cycle
    pos_r = {"A": (-0.5, 0), "B": (0.5, 0)}
    # G: larger graph including the cycle
    pos_g = {
        "Alice": (-0.6, 0.4), "Bob": (0.6, 0.4),
        "Carol": (0, -0.6), "Dave": (-0.9, -0.4),
    }
    edges_g = [("Alice", "Bob"), ("Bob", "Alice"), ("Bob", "Carol"),
               ("Carol", "Dave"), ("Dave", "Alice")]
    highlight_g = {("Alice", "Bob"), ("Bob", "Alice")}

    def draw_small(ax, title, nodes_pos, edges, highlight=None):
        for u, v in edges:
            is_hl = highlight and (u, v) in highlight
            _arrow(ax, nodes_pos[u], nodes_pos[v],
                   color="#e74c3c" if is_hl else "#95a5a6",
                   lw=2.5 if is_hl else 1.2, rad=0.2)
        for nd, (x, y) in nodes_pos.items():
            is_hl = highlight and any(nd in e for e in highlight)
            color = "#e74c3c" if is_hl else "#3498db"
            circle = plt.Circle((x, y), 0.13, color=color, zorder=3)
            ax.add_patch(circle)
            ax.text(x, y, nd, ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold", zorder=4)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.1, 1.1)

    draw_small(axes[0], titles[0], pos_r, [("A", "B"), ("B", "A")])
    draw_small(axes[1], titles[1], pos_g, edges_g)
    draw_small(axes[2], titles[2], pos_g, edges_g, highlight=highlight_g)

    # Add "⊆" arrow between subplots
    fig.text(0.35, 0.48, "?  ⊆  ?", ha="center", fontsize=16, color="#2c3e50")
    fig.text(0.67, 0.48, "✓  erkannt", ha="center", fontsize=13, color="#27ae60", fontweight="bold")

    fig.suptitle('subgraph_contains(R, G) → decision="keep_B" → Muster erkannt',
                 fontsize=12, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "subgraph_overview")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 12.  Max-Flow Network
# ─────────────────────────────────────────────────────────────────────────────
def fig_max_flow():
    nodes = ["Gehalt", "Konto", "Sparplan", "Invest", "Reserve", "Ausgaben"]
    # (source, target, capacity, flow)
    edges = [
        ("Gehalt",  "Konto",   3200, 3200),
        ("Konto",   "Sparplan", 500,  500),
        ("Konto",   "Invest",  1000,  800),
        ("Konto",   "Reserve",  500,  300),
        ("Konto",   "Ausgaben", 1500, 1500),
        ("Sparplan","Invest",   200,  100),
    ]
    pos = {
        "Gehalt":   (-1.2, 0),
        "Konto":    (-0.2, 0),
        "Sparplan": (0.7,  0.8),
        "Invest":   (0.7,  0.0),
        "Reserve":  (0.7, -0.8),
        "Ausgaben": (1.8,  0.0),
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    max_cap = max(c for _, _, c, _ in edges)
    for src, dst, cap, flow in edges:
        lw = 0.5 + 3.5 * cap / max_cap
        utilization = flow / cap
        color = "#e74c3c" if utilization > 0.8 else "#3498db" if utilization > 0.4 else "#2ecc71"
        _arrow(ax, pos[src], pos[dst], color=color, lw=lw, rad=0.08)
        mx = (pos[src][0] + pos[dst][0]) / 2
        my = (pos[src][1] + pos[dst][1]) / 2 + 0.1
        ax.text(mx, my, f"{flow}/{cap}€", fontsize=8.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.85, edgecolor="none"))

    for nd, (x, y) in pos.items():
        is_source = nd == "Gehalt"
        is_sink = nd == "Ausgaben"
        color = "#27ae60" if is_source else "#e74c3c" if is_sink else "#2c3e50"
        circle = plt.Circle((x, y), 0.14, color=color, zorder=3)
        ax.add_patch(circle)
        lbl = nd if len(nd) <= 7 else nd[:6] + "."
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=8, color="white", fontweight="bold", zorder=4)

    legend = [
        mpatches.Patch(color="#27ae60", label="Quelle"),
        mpatches.Patch(color="#e74c3c", label="Senke / hoch ausgelastet"),
        mpatches.Patch(color="#3498db", label="Mittel ausgelastet"),
        mpatches.Patch(color="#2ecc71", label="Gering ausgelastet"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=9)
    ax.set_title("Cashflow-Netzwerk: Max-Flow (Edmonds-Karp)\nFluss/Kapazität pro Kante",
                 fontsize=12, fontweight="bold")
    ax.set_aspect("equal"); ax.set_xlim(-1.7, 2.3); ax.set_ylim(-1.3, 1.3)
    ax.axis("off")
    fig.tight_layout()
    _save(fig, "max_flow")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 13.  Architecture Overview
# ─────────────────────────────────────────────────────────────────────────────
def fig_architecture():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")

    boxes = {
        # (x, y, width, height, label, color)
        "GUI\n(PyQt6)":           (0.5, 0.72, 0.20, 0.18, "#2980b9"),
        "Visualization\n(Matplotlib)": (0.5, 0.46, 0.20, 0.18, "#8e44ad"),
        "Analysis\n(Markowitz, VaR)":  (0.20, 0.20, 0.18, 0.18, "#27ae60"),
        "Algorithms\n(Graph, MST, …)": (0.50, 0.20, 0.18, 0.18, "#e67e22"),
        "Core\n(Account, Portfolio…)": (0.78, 0.20, 0.18, 0.18, "#c0392b"),
        "subgraph\n(Extern)":          (0.50, -0.04, 0.18, 0.14, "#7f8c8d"),
    }

    for lbl, (x, y, w, h, col) in boxes.items():
        rect = mpatches.FancyBboxPatch(
            (x - w / 2, y), w, h,
            boxstyle="round,pad=0.02", facecolor=col, edgecolor="white",
            linewidth=1.5, zorder=2, alpha=0.9,
        )
        ax.add_patch(rect)
        ax.text(x, y + h / 2, lbl, ha="center", va="center",
                fontsize=9.5, color="white", fontweight="bold", zorder=3)

    # Arrows
    arrow_kw = dict(arrowstyle="-|>", color="#2c3e50", lw=1.5)
    connections = [
        ((0.5, 0.72), (0.5, 0.64)),               # GUI -> Visualization
        ((0.5, 0.46), (0.32, 0.38)),               # Visualization -> Analysis
        ((0.5, 0.46), (0.52, 0.38)),               # Visualization -> Algorithms
        ((0.5, 0.46), (0.80, 0.38)),               # Visualization -> Core
        ((0.5, 0.72), (0.23, 0.38)),               # GUI -> Analysis
        ((0.5, 0.72), (0.81, 0.38)),               # GUI -> Core
        ((0.52, 0.20), (0.52, 0.10)),              # Algorithms -> subgraph
    ]
    for (x1, y1), (x2, y2) in connections:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops={**arrow_kw, "connectionstyle": "arc3,rad=0.0"})

    ax.set_xlim(0, 1); ax.set_ylim(-0.15, 1.05)
    ax.set_title("FyLab Modularchitektur – Schichtenmodell", fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "architecture")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generating figures → {OUT}/  (png + svg + pdf)")
    fig_cashflow_waterfall()
    fig_asset_allocation()
    fig_efficient_frontier()
    fig_portfolio_mst()
    fig_monte_carlo()
    fig_transaction_graph()
    fig_fraud_patterns()
    fig_arbitrage()
    fig_debt_simplification()
    fig_var_distribution()
    fig_subgraph_overview()
    fig_max_flow()
    fig_architecture()
    print("Done.")
