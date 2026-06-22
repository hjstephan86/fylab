"""
tests.test_visualization
==========================
100 % Coverage für fylab.visualization:
  - cashflow_chart  (plot_cashflow_waterfall, plot_income_expense)
  - graph_viz       (plot_transaction_graph, plot_portfolio_mst,
                     plot_risk_monte_carlo)
  - portfolio_chart (plot_asset_allocation, plot_efficient_frontier)
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")          # headless – kein Display erforderlich
import matplotlib.pyplot as plt
import numpy as np
import pytest
from dataclasses import dataclass
from datetime import date

from fylab.core.account import Account, AccountType, Transaction, TransactionCategory
from fylab.core.portfolio import Portfolio, Position, Asset, AssetClass
from fylab.core.cashflow import CashflowPlan, CashflowItem, Frequency
from fylab.algorithms.mst import MSTResult
from fylab.algorithms.subgraph_finance import FraudDetectionResult, FraudPattern
from fylab.analysis.portfolio_opt import EfficientFrontierResult

from fylab.visualization.cashflow_chart import plot_cashflow_waterfall, plot_income_expense
from fylab.visualization.graph_viz import (
    plot_transaction_graph,
    plot_portfolio_mst,
    plot_risk_monte_carlo,
)
from fylab.visualization.portfolio_chart import (
    plot_asset_allocation,
    plot_efficient_frontier,
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_account_with_txns() -> Account:
    acc = Account("V001", "Visualisierungskonto", AccountType.CHECKING, initial_balance=1_000.0)
    entries = [
        (date(2026, 1, 10),  2_500.0,  "Gehalt Jan",   TransactionCategory.INCOME),
        (date(2026, 1, 20),   -800.0,  "Miete Jan",    TransactionCategory.EXPENSE),
        (date(2026, 2, 10),  2_500.0,  "Gehalt Feb",   TransactionCategory.INCOME),
        (date(2026, 2, 22),   -300.0,  "Gas Feb",      TransactionCategory.EXPENSE),
        (date(2026, 3, 10),  2_500.0,  "Gehalt Mär",   TransactionCategory.INCOME),
        (date(2026, 3, 15),   -500.0,  "Investition",  TransactionCategory.INVESTMENT),
    ]
    for d, amt, desc, cat in entries:
        acc.add_transaction(Transaction(d, amt, desc, cat, acc.account_id))
    return acc


def _make_cashflow_plan() -> CashflowPlan:
    plan = CashflowPlan("Testplan")
    plan.items = [
        CashflowItem("Gehalt",    3_000.0,  date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Miete",      -900.0,  date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Nebenkosten",-150.0,  date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Bonus",     5_000.0,  date(2026, 6, 1),  Frequency.ONCE),
    ]
    return plan


def _make_portfolio() -> Portfolio:
    pf = Portfolio("TestDepot")
    items = [
        (Asset("MSFT", "Microsoft",  AssetClass.STOCK),  5, 380.0, 420.0),
        (Asset("AAPL", "Apple",      AssetClass.STOCK), 10, 160.0, 185.0),
        (Asset("GOVB", "Bundesanl.", AssetClass.BOND),  50,  98.0, 101.0),
        (Asset("CASH", "Liquidität", AssetClass.CASH),   1,   1.0,   1.0),
    ]
    for asset, qty, buy, price in items:
        pf.positions.append(Position(asset=asset, quantity=qty,
                                     avg_buy_price=buy, current_price=price))
    return pf


def _make_mst_result(n_nodes: int = 4) -> MSTResult:
    nodes = [chr(65 + i) for i in range(n_nodes)]   # "A", "B", ...
    edges = [(nodes[i], nodes[i + 1], 0.3 + i * 0.1)
             for i in range(n_nodes - 1)]
    clusters = [[n] for n in nodes]
    return MSTResult(
        nodes=nodes,
        edges=edges,
        total_weight=sum(w for _, _, w in edges),
        clusters=clusters,
    )


def _make_frontier_result(n: int = 80) -> EfficientFrontierResult:
    rng = np.random.default_rng(0)
    rets = rng.uniform(0.05, 0.20, n)
    vols = rng.uniform(0.10, 0.35, n)
    sharpes = rets / vols
    best_idx = int(np.argmax(sharpes))
    return EfficientFrontierResult(
        returns=rets,
        volatilities=vols,
        sharpe_ratios=sharpes,
        optimal_weights=np.array([0.4, 0.3, 0.3]),
        optimal_return=float(rets[best_idx]),
        optimal_volatility=float(vols[best_idx]),
        optimal_sharpe=float(sharpes[best_idx]),
    )


def _close_all() -> None:
    plt.close("all")


# ===========================================================================
# cashflow_chart
# ===========================================================================

class TestPlotCashflowWaterfall:
    """plot_cashflow_waterfall: positive und negative Monatswerte."""

    def test_returns_figure(self):
        plan = _make_cashflow_plan()
        fig = plot_cashflow_waterfall(plan, 2026)
        assert fig is not None
        _close_all()

    def test_figure_has_two_axes(self):
        plan = _make_cashflow_plan()
        fig = plot_cashflow_waterfall(plan, 2026)
        assert len(fig.axes) == 2
        _close_all()

    def test_with_only_negative_values(self):
        """Erzwingt ausschließlich rote Balken."""
        plan = CashflowPlan("Nur Ausgaben")
        plan.items = [
            CashflowItem("Miete", -1_200.0, date(2026, 1, 1),
                         Frequency.MONTHLY, date(2026, 12, 31)),
        ]
        fig = plot_cashflow_waterfall(plan, 2026)
        assert fig is not None
        _close_all()

    def test_with_only_positive_values(self):
        """Erzwingt ausschließlich grüne Balken."""
        plan = CashflowPlan("Nur Einnahmen")
        plan.items = [
            CashflowItem("Gehalt", 3_000.0, date(2026, 1, 1),
                         Frequency.MONTHLY, date(2026, 12, 31)),
        ]
        fig = plot_cashflow_waterfall(plan, 2026)
        assert fig is not None
        _close_all()

    def test_empty_plan(self):
        """Plan ohne Posten liefert alles-Null-Cashflow."""
        plan = CashflowPlan("Leer")
        plan.items = []
        fig = plot_cashflow_waterfall(plan, 2026)
        assert fig is not None
        _close_all()


class TestPlotIncomeExpense:
    """plot_income_expense: Einnahmen-/Ausgaben-Balkendiagramm."""

    def test_returns_figure(self):
        acc = _make_account_with_txns()
        fig = plot_income_expense(acc)
        assert fig is not None
        _close_all()

    def test_has_one_axis(self):
        acc = _make_account_with_txns()
        fig = plot_income_expense(acc)
        assert len(fig.axes) == 1
        _close_all()

    def test_empty_account(self):
        """Konto ohne Buchungen → leere Monatsübersicht."""
        acc = Account("E002", "Leer", AccountType.SAVINGS)
        fig = plot_income_expense(acc)
        assert fig is not None
        _close_all()

    def test_single_month(self):
        acc = Account("S001", "Einmonat", AccountType.CHECKING, initial_balance=0.0)
        acc.add_transaction(
            Transaction(date(2026, 5, 1), 1_000.0, "Einzahlung",
                        TransactionCategory.INCOME, "S001"))
        acc.add_transaction(
            Transaction(date(2026, 5, 15), -200.0, "Ausgabe",
                        TransactionCategory.EXPENSE, "S001"))
        fig = plot_income_expense(acc)
        assert fig is not None
        _close_all()


# ===========================================================================
# graph_viz
# ===========================================================================

class TestPlotTransactionGraph:
    """plot_transaction_graph: leerer Graph, Einzelknoten, Fraud-Ergebnisse."""

    def test_empty_graph(self):
        """`_circular_layout` mit n=0."""
        fig = plot_transaction_graph({})
        assert fig is not None
        _close_all()

    def test_single_node_no_edges(self):
        """`_circular_layout` mit n=1; leere targets-dict."""
        fig = plot_transaction_graph({"Alice": {}})
        assert fig is not None
        _close_all()

    def test_two_nodes_single_edge(self):
        fig = plot_transaction_graph({"Alice": {"Bob": 500.0}})
        assert fig is not None
        _close_all()

    def test_cycle_graph(self):
        """Gerichteter Zyklus – Kanten werden gebogen gezeichnet."""
        graph = {
            "Alice": {"Bob": 1_000.0},
            "Bob":   {"Carol": 800.0},
            "Carol": {"Alice": 600.0},
        }
        fig = plot_transaction_graph(graph, fraud_results=None, title="Zyklus")
        assert fig is not None
        _close_all()

    def test_fraud_not_detected(self):
        """fraud_results vorhanden, aber keine Erkennung → keine roten Knoten."""
        graph = {"Alice": {"Bob": 300.0}}
        fr = FraudDetectionResult(
            pattern=FraudPattern.SMURFING,
            detected=False,
            decision="keep_both",
            mapping=None,
        )
        fig = plot_transaction_graph(graph, fraud_results=[fr])
        assert fig is not None
        _close_all()

    def test_fraud_detected_with_mapping(self):
        """Erkannte Betrugsknoten werden rot eingefärbt."""
        graph = {
            "Alice": {"Bob": 500.0},
            "Bob":   {"Alice": 450.0},
        }
        fr = FraudDetectionResult(
            pattern=FraudPattern.WASH_TRADING,
            detected=True,
            decision="equal_keep_A",
            mapping={"Alice": 0, "Bob": 1},
        )
        fig = plot_transaction_graph(graph, fraud_results=[fr])
        assert fig is not None
        _close_all()

    def test_fraud_detected_no_mapping(self):
        """Erkannt aber mapping=None → keine roten Knoten."""
        graph = {"X": {"Y": 100.0}}
        fr = FraudDetectionResult(
            pattern=FraudPattern.LAYERING,
            detected=True,
            decision="equal_keep_A",
            mapping=None,
        )
        fig = plot_transaction_graph(graph, fraud_results=[fr])
        assert fig is not None
        _close_all()

    def test_large_graph_all_helpers_called(self):
        """Stellt sicher, dass _draw_node/_draw_directed_edge/_draw_edge_label
        für mehrere Knoten aufgerufen werden."""
        graph = {
            "A": {"B": 100.0, "C": 200.0, "D": 50.0},
            "B": {"C": 150.0, "D": 80.0},
            "C": {"A": 90.0},
            "D": {"E": 30.0},
        }
        fig = plot_transaction_graph(graph, title="Großer Graph")
        assert fig is not None
        _close_all()


class TestPlotPortfolioMST:
    """plot_portfolio_mst: verschiedene Knotenanzahlen und Cluster-Färbung."""

    def test_basic_four_nodes(self):
        mst = _make_mst_result(4)
        fig = plot_portfolio_mst(mst)
        assert fig is not None
        _close_all()

    def test_default_title(self):
        mst = _make_mst_result(3)
        fig = plot_portfolio_mst(mst)
        assert "Portfolio-MST" in fig.axes[0].get_title()
        _close_all()

    def test_custom_title(self):
        mst = _make_mst_result(3)
        fig = plot_portfolio_mst(mst, title="Mein MST")
        assert "Mein MST" in fig.axes[0].get_title()
        _close_all()

    def test_single_node_no_edges(self):
        """`_circular_layout` mit n=1."""
        mst = MSTResult(nodes=["Solo"], edges=[], total_weight=0.0, clusters=[["Solo"]])
        fig = plot_portfolio_mst(mst)
        assert fig is not None
        _close_all()

    def test_many_clusters_cycles_palette(self):
        """Mehr Cluster als Palette-Einträge (Set2 hat 8 Farben) → Modulo-Zugriff."""
        n = 10
        nodes = [chr(65 + i) for i in range(n)]
        edges = [(nodes[i], nodes[i + 1], 0.5) for i in range(n - 1)]
        mst = MSTResult(
            nodes=nodes,
            edges=edges,
            total_weight=float(n - 1) * 0.5,
            clusters=[[node] for node in nodes],   # 10 Cluster → überschreitet 8
        )
        fig = plot_portfolio_mst(mst)
        assert fig is not None
        _close_all()

    def test_node_not_in_palette_fallback(self):
        """Knoten ohne Cluster-Zugehörigkeit bekommt Fallback-Farbe."""
        mst = MSTResult(
            nodes=["A", "B"],
            edges=[("A", "B", 0.3)],
            total_weight=0.3,
            clusters=[],        # kein Cluster → node_color_map bleibt leer
        )
        fig = plot_portfolio_mst(mst)
        assert fig is not None
        _close_all()


class TestPlotRiskMonteCarlo:
    """plot_risk_monte_carlo: Pfade, Quantile, Titel."""

    def test_standard_simulation(self):
        rng = np.random.default_rng(42)
        sims = rng.uniform(90_000, 110_000, (500, 252))
        fig = plot_risk_monte_carlo(sims, "Monte-Carlo Test")
        assert fig is not None
        _close_all()

    def test_default_title(self):
        rng = np.random.default_rng(1)
        sims = rng.uniform(80_000, 120_000, (50, 30))
        fig = plot_risk_monte_carlo(sims)
        assert "Monte-Carlo" in fig.axes[0].get_title()
        _close_all()

    def test_fewer_than_200_simulations(self):
        """min(200, n_sim) = n_sim-Zweig."""
        rng = np.random.default_rng(7)
        sims = rng.uniform(100_000, 200_000, (100, 50))
        fig = plot_risk_monte_carlo(sims)
        assert fig is not None
        _close_all()

    def test_more_than_200_simulations(self):
        """min(200, n_sim) = 200-Zweig."""
        rng = np.random.default_rng(99)
        sims = rng.uniform(50_000, 150_000, (300, 40))
        fig = plot_risk_monte_carlo(sims)
        assert fig is not None
        _close_all()


# ===========================================================================
# portfolio_chart
# ===========================================================================

class TestPlotAssetAllocation:
    """plot_asset_allocation: Tortendiagramm."""

    def test_returns_figure(self):
        pf = _make_portfolio()
        fig = plot_asset_allocation(pf)
        assert fig is not None
        _close_all()

    def test_single_asset_class(self):
        pf = Portfolio("AllStocks")
        pf.positions = [
            Position(asset=Asset("X", "X-Corp", AssetClass.STOCK),
                     quantity=1, avg_buy_price=100.0, current_price=110.0),
        ]
        fig = plot_asset_allocation(pf)
        assert fig is not None
        _close_all()


class TestPlotEfficientFrontier:
    """plot_efficient_frontier: mit und ohne optionale Asset-Scatter-Parameter."""

    def test_without_optional_args(self):
        result = _make_frontier_result()
        fig = plot_efficient_frontier(result)
        assert fig is not None
        _close_all()

    def test_with_all_optional_args(self):
        """Deckt den `if asset_vols is not None and ...`-Zweig ab."""
        result = _make_frontier_result(50)
        symbols = ["MSFT", "AAPL", "NVDA"]
        asset_vols = np.array([0.18, 0.22, 0.30])
        asset_rets = np.array([0.10, 0.12, 0.17])
        fig = plot_efficient_frontier(result, symbols, asset_vols, asset_rets)
        assert fig is not None
        _close_all()

    def test_with_only_symbols_no_scatter(self):
        """symbols gesetzt, aber vols/rets fehlen → Scatter-Block nicht ausgeführt."""
        result = _make_frontier_result()
        fig = plot_efficient_frontier(result, symbols=["A", "B"])
        assert fig is not None
        _close_all()

    def test_optimal_marked(self):
        result = _make_frontier_result(60)
        fig = plot_efficient_frontier(result)
        ax = fig.axes[0]
        # Sicherstellen, dass roter Stern (optimales Portfolio) eingezeichnet
        scatter_artists = ax.collections
        assert len(scatter_artists) >= 2   # Frontier + Optimum
        _close_all()
