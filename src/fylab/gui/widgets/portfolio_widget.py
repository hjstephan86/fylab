"""
fylab.gui.widgets.portfolio_widget
=====================================
Portfolio-Übersicht: Positionen, Allokation, Effizienzgrenze.
"""

from __future__ import annotations

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QTabWidget,
    QHeaderView, QSplitter,
)
from PyQt6.QtCore import Qt

from fylab.core.portfolio import Portfolio, Position, Asset, AssetClass
from fylab.analysis.portfolio_opt import compute_efficient_frontier, compute_diversification_mst
from fylab.visualization.portfolio_chart import plot_asset_allocation, plot_efficient_frontier
from fylab.visualization.graph_viz import plot_portfolio_mst
from fylab.gui.widgets.plot_widget import PlotWidget


def _demo_portfolio() -> Portfolio:
    assets = [
        Asset("MSFT", "Microsoft", AssetClass.STOCK),
        Asset("AAPL", "Apple", AssetClass.STOCK),
        Asset("NVDA", "NVIDIA", AssetClass.STOCK),
        Asset("EWG.DE", "iShares MSCI Germany", AssetClass.ETF),
        Asset("VWRL.L", "Vanguard All World", AssetClass.ETF),
        Asset("BTC", "Bitcoin", AssetClass.CRYPTO),
        Asset("EUR_CASH", "Liquidität EUR", AssetClass.CASH),
    ]
    prices = [420.0, 185.0, 875.0, 32.0, 108.0, 65000.0, 1.0]
    qtys = [5, 15, 3, 100, 80, 0.05, 2500]
    buys = [380.0, 170.0, 650.0, 30.0, 100.0, 45000.0, 1.0]

    portfolio = Portfolio("Mein Depot")
    for asset, qty, buy, price in zip(assets, qtys, buys, prices):
        portfolio.positions.append(
            Position(asset=asset, quantity=qty, avg_buy_price=buy, current_price=price)
        )
    return portfolio


class PortfolioWidget(QWidget):
    """Portfolio-Übersicht mit Tabs für Positionen / Allokation / Effizienzgrenze / MST."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._portfolio = _demo_portfolio()
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Kopfzeile
        header = QHBoxLayout()
        self._lbl_total = QLabel()
        self._lbl_total.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._lbl_pnl = QLabel()
        header.addWidget(QLabel("Portfolio:"))
        header.addWidget(self._lbl_total)
        header.addStretch()
        header.addWidget(QLabel("G/V:"))
        header.addWidget(self._lbl_pnl)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Positionen
        tab_pos = QWidget()
        tl = QVBoxLayout(tab_pos)
        self._pos_table = QTableWidget()
        self._pos_table.setColumnCount(7)
        self._pos_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Klasse", "Menge", "Kurs (€)", "Wert (€)", "G/V (%)"
        ])
        self._pos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._pos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._pos_table.setAlternatingRowColors(True)
        tl.addWidget(self._pos_table)
        tabs.addTab(tab_pos, "Positionen")

        # Tab 2: Allokation
        tab_alloc = QWidget()
        al = QVBoxLayout(tab_alloc)
        self._plot_alloc = PlotWidget()
        al.addWidget(self._plot_alloc)
        tabs.addTab(tab_alloc, "Allokation")

        # Tab 3: Effizienzgrenze
        tab_ef = QWidget()
        el = QVBoxLayout(tab_ef)
        btn_ef = QPushButton("Effizienzgrenze berechnen")
        btn_ef.clicked.connect(self._compute_frontier)
        el.addWidget(btn_ef)
        self._plot_ef = PlotWidget()
        el.addWidget(self._plot_ef)
        tabs.addTab(tab_ef, "Effizienzgrenze")

        # Tab 4: MST
        tab_mst = QWidget()
        ml = QVBoxLayout(tab_mst)
        btn_mst = QPushButton("Portfolio-MST berechnen")
        btn_mst.clicked.connect(self._compute_mst)
        ml.addWidget(btn_mst)
        self._plot_mst = PlotWidget()
        ml.addWidget(self._plot_mst)
        tabs.addTab(tab_mst, "MST Diversifikation")

    def _refresh(self) -> None:
        pf = self._portfolio
        self._lbl_total.setText(f"{pf.total_value:,.2f} €")
        pnl = pf.total_profit_loss
        color = "#27ae60" if pnl >= 0 else "#e74c3c"
        self._lbl_pnl.setStyleSheet(f"color: {color};")
        self._lbl_pnl.setText(f"{pnl:+,.2f} €")

        # Tabelle befüllen
        self._pos_table.setRowCount(len(pf.positions))
        for row, pos in enumerate(pf.positions):
            self._pos_table.setItem(row, 0, QTableWidgetItem(pos.asset.symbol))
            self._pos_table.setItem(row, 1, QTableWidgetItem(pos.asset.name))
            self._pos_table.setItem(row, 2, QTableWidgetItem(pos.asset.asset_class.value))
            self._pos_table.setItem(row, 3, QTableWidgetItem(f"{pos.quantity:.4f}"))
            self._pos_table.setItem(row, 4, QTableWidgetItem(f"{pos.current_price:,.2f}"))
            val_item = QTableWidgetItem(f"{pos.market_value:,.2f}")
            val_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._pos_table.setItem(row, 5, val_item)
            pnl_pct = pos.profit_loss_pct
            pnl_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            from PyQt6.QtGui import QColor
            pnl_item.setForeground(QColor("#27ae60") if pnl_pct >= 0 else QColor("#e74c3c"))
            pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._pos_table.setItem(row, 6, pnl_item)

        # Allokations-Chart
        fig_alloc = plot_asset_allocation(pf)
        self._plot_alloc.set_figure(fig_alloc)

    def _compute_frontier(self) -> None:
        positions = [p for p in self._portfolio.positions
                     if p.asset.asset_class != AssetClass.CASH]
        n = len(positions)
        rng = np.random.default_rng(42)
        symbols = [p.asset.symbol for p in positions]
        expected_returns = rng.uniform(0.04, 0.20, n)
        # Zufällige, aber positiv definite Kovarianzmatrix
        A = rng.standard_normal((n, n))
        cov = A @ A.T / n * 0.04
        result = compute_efficient_frontier(symbols, expected_returns, cov)
        vols = np.sqrt(np.diag(cov))
        fig = plot_efficient_frontier(result, symbols, vols, expected_returns)
        self._plot_ef.set_figure(fig)

    def _compute_mst(self) -> None:
        positions = [p for p in self._portfolio.positions
                     if p.asset.asset_class not in (AssetClass.CASH,)]
        n = len(positions)
        rng = np.random.default_rng(123)
        symbols = [p.asset.symbol for p in positions]
        # Synthetische Korrelationsmatrix
        A = rng.uniform(-1, 1, (n, n))
        corr = (A + A.T) / 2
        np.fill_diagonal(corr, 1.0)
        # Auf [-1, 1] klemmen
        corr = np.clip(corr, -0.99, 0.99)
        mst_result = compute_diversification_mst(symbols, corr)
        fig = plot_portfolio_mst(mst_result)
        self._plot_mst.set_figure(fig)
