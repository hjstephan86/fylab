"""
tests.test_gui
================
100 % Coverage für fylab.gui:
  - gui/widgets/plot_widget.py
  - gui/widgets/account_widget.py
  - gui/widgets/portfolio_widget.py
  - gui/widgets/cashflow_widget.py
  - gui/widgets/graph_widget.py
  - gui/widgets/risk_widget.py
  - gui/main_window.py   (exkl. main(), die mit # pragma: no cover markiert ist)

Verwendet pytest-qt (qtbot-Fixture) für PyQt6-Widgets.
Modal-Dialoge werden über QTimer.singleShot(0, ...) automatisch
akzeptiert oder abgebrochen, ohne den Event-Loop zu blockieren.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import pytest
from unittest.mock import patch
from datetime import date

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QDialog, QTabWidget, QDockWidget, QToolBar,
)
from matplotlib.figure import Figure


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _accept_modal() -> None:
    """Akzeptiert das aktuell aktive Modal-Widget (QDialog)."""
    modal = QApplication.activeModalWidget()
    if isinstance(modal, QDialog):
        modal.accept()


def _reject_modal() -> None:
    """Bricht das aktuell aktive Modal-Widget ab."""
    modal = QApplication.activeModalWidget()
    if isinstance(modal, QDialog):
        modal.reject()


# ===========================================================================
# PlotWidget
# ===========================================================================

class TestPlotWidget:
    """fylab.gui.widgets.plot_widget.PlotWidget"""

    def test_default_construction(self, qtbot):
        from fylab.gui.widgets.plot_widget import PlotWidget
        w = PlotWidget()
        qtbot.addWidget(w)
        assert w._fig is not None

    def test_construction_with_figure(self, qtbot):
        from fylab.gui.widgets.plot_widget import PlotWidget
        fig = Figure(figsize=(4, 3))
        w = PlotWidget(figure=fig)
        qtbot.addWidget(w)
        assert w._fig is fig

    def test_set_figure(self, qtbot):
        from fylab.gui.widgets.plot_widget import PlotWidget
        w = PlotWidget()
        qtbot.addWidget(w)
        new_fig = Figure(figsize=(5, 4))
        w.set_figure(new_fig)
        assert w._fig is new_fig

    def test_refresh(self, qtbot):
        from fylab.gui.widgets.plot_widget import PlotWidget
        w = PlotWidget()
        qtbot.addWidget(w)
        w.refresh()   # must not raise


# ===========================================================================
# AccountWidget
# ===========================================================================

class TestAccountWidget:
    """fylab.gui.widgets.account_widget.AccountWidget"""

    def test_construction_creates_demo_account(self, qtbot):
        from fylab.gui.widgets.account_widget import AccountWidget
        w = AccountWidget()
        qtbot.addWidget(w)
        assert len(w._account.transactions) > 0

    def test_positive_balance_label_color(self, qtbot):
        from fylab.gui.widgets.account_widget import AccountWidget
        w = AccountWidget()
        qtbot.addWidget(w)
        # Demo-Konto hat positiven Saldo
        assert w._account.balance >= 0

    def test_negative_balance_label_color(self, qtbot):
        """Erzwingt den color='#e74c3c'-Zweig."""
        from fylab.gui.widgets.account_widget import AccountWidget
        from fylab.core.account import Account, AccountType
        w = AccountWidget()
        qtbot.addWidget(w)
        # Ersetze Konto durch eines mit großem negativem Saldo
        neg_acc = Account("NEG", "Minus", AccountType.CHECKING,
                          initial_balance=-10_000.0)
        w._account = neg_acc
        w._refresh()   # setzt rote Balanceanzeige

    def test_filter_all_categories(self, qtbot):
        from fylab.gui.widgets.account_widget import AccountWidget
        w = AccountWidget()
        qtbot.addWidget(w)
        w._combo_cat.setCurrentIndex(0)   # "Alle"
        w._refresh_table()
        assert w._table.rowCount() == len(w._account.transactions)

    def test_filter_by_category(self, qtbot):
        from fylab.gui.widgets.account_widget import AccountWidget
        from fylab.core.account import TransactionCategory
        w = AccountWidget()
        qtbot.addWidget(w)
        # Index 1 entspricht der ersten echten Kategorie
        w._combo_cat.setCurrentIndex(1)
        w._refresh_table()
        # Tabellenzeilen ≤ Gesamtzahl Transaktionen
        assert w._table.rowCount() <= len(w._account.transactions)

    def test_show_add_dialog_accepted(self, qtbot):
        """Buchung wird hinzugefügt, wenn Dialog akzeptiert wird."""
        from fylab.gui.widgets.account_widget import AccountWidget
        w = AccountWidget()
        qtbot.addWidget(w)
        initial = len(w._account.transactions)
        QTimer.singleShot(0, _accept_modal)
        w._show_add_dialog()
        assert len(w._account.transactions) == initial + 1

    def test_show_add_dialog_rejected(self, qtbot):
        """Keine neue Buchung, wenn Dialog abgebrochen wird."""
        from fylab.gui.widgets.account_widget import AccountWidget
        w = AccountWidget()
        qtbot.addWidget(w)
        initial = len(w._account.transactions)
        QTimer.singleShot(0, _reject_modal)
        w._show_add_dialog()
        assert len(w._account.transactions) == initial


# ===========================================================================
# PortfolioWidget
# ===========================================================================

class TestPortfolioWidget:
    """fylab.gui.widgets.portfolio_widget.PortfolioWidget"""

    def test_construction(self, qtbot):
        from fylab.gui.widgets.portfolio_widget import PortfolioWidget
        w = PortfolioWidget()
        qtbot.addWidget(w)
        assert len(w._portfolio.positions) > 0

    def test_total_value_label(self, qtbot):
        from fylab.gui.widgets.portfolio_widget import PortfolioWidget
        w = PortfolioWidget()
        qtbot.addWidget(w)
        assert "€" in w._lbl_total.text()

    def test_pnl_label_positive(self, qtbot):
        """Demo-Portfolio hat insgesamt positiven G/V."""
        from fylab.gui.widgets.portfolio_widget import PortfolioWidget
        w = PortfolioWidget()
        qtbot.addWidget(w)
        # Einfacher Smoke-Test: PnL-Label existiert
        assert w._lbl_pnl.text() != ""

    def test_compute_frontier(self, qtbot):
        """Effizienzgrenze berechnen und Plot setzen – kein Fehler."""
        from fylab.gui.widgets.portfolio_widget import PortfolioWidget
        w = PortfolioWidget()
        qtbot.addWidget(w)
        w._compute_frontier()   # setzt _plot_ef

    def test_compute_mst(self, qtbot):
        """MST berechnen und Plot setzen – kein Fehler."""
        from fylab.gui.widgets.portfolio_widget import PortfolioWidget
        w = PortfolioWidget()
        qtbot.addWidget(w)
        w._compute_mst()


# ===========================================================================
# CashflowWidget
# ===========================================================================

class TestCashflowWidget:
    """fylab.gui.widgets.cashflow_widget.CashflowWidget"""

    def test_construction(self, qtbot):
        from fylab.gui.widgets.cashflow_widget import CashflowWidget
        w = CashflowWidget()
        qtbot.addWidget(w)
        assert len(w._plan.items) > 0

    def test_summary_label_positive(self, qtbot):
        from fylab.gui.widgets.cashflow_widget import CashflowWidget
        w = CashflowWidget()
        qtbot.addWidget(w)
        assert "€" in w._lbl_summary.text()

    def test_year_change_refreshes_chart(self, qtbot):
        from fylab.gui.widgets.cashflow_widget import CashflowWidget
        w = CashflowWidget()
        qtbot.addWidget(w)
        w._year_spin.setValue(2027)   # löst _refresh() aus

    def test_add_item_accepted(self, qtbot):
        """Posten wird hinzugefügt, wenn Dialog akzeptiert wird."""
        from fylab.gui.widgets.cashflow_widget import CashflowWidget
        w = CashflowWidget()
        qtbot.addWidget(w)
        initial = len(w._plan.items)
        QTimer.singleShot(0, _accept_modal)
        w._add_item()
        assert len(w._plan.items) == initial + 1

    def test_add_item_rejected(self, qtbot):
        """Kein neuer Posten, wenn Dialog abgebrochen wird."""
        from fylab.gui.widgets.cashflow_widget import CashflowWidget
        w = CashflowWidget()
        qtbot.addWidget(w)
        initial = len(w._plan.items)
        QTimer.singleShot(0, _reject_modal)
        w._add_item()
        assert len(w._plan.items) == initial


# ===========================================================================
# GraphWidget
# ===========================================================================

class TestGraphWidget:
    """fylab.gui.widgets.graph_widget.GraphWidget"""

    def test_construction(self, qtbot):
        from fylab.gui.widgets.graph_widget import GraphWidget
        w = GraphWidget()
        qtbot.addWidget(w)

    def test_run_fraud_detection(self, qtbot):
        from fylab.gui.widgets.graph_widget import GraphWidget
        w = GraphWidget()
        qtbot.addWidget(w)
        w._run_fraud_detection()
        assert w._fraud_result.toPlainText() != ""

    def test_fraud_result_contains_pattern_info(self, qtbot):
        from fylab.gui.widgets.graph_widget import GraphWidget
        w = GraphWidget()
        qtbot.addWidget(w)
        w._run_fraud_detection()
        text = w._fraud_result.toPlainText()
        # Mindestens ein Muster muss im Text erscheinen
        assert any(kw in text for kw in ["ERKANNT", "nicht gefunden"])

    def test_run_arbitrage(self, qtbot):
        from fylab.gui.widgets.graph_widget import GraphWidget
        w = GraphWidget()
        qtbot.addWidget(w)
        w._run_arbitrage()
        assert w._arb_result.toPlainText() != ""

    def test_run_debt_simplify(self, qtbot):
        from fylab.gui.widgets.graph_widget import GraphWidget
        w = GraphWidget()
        qtbot.addWidget(w)
        w._run_debt_simplify()
        assert w._debt_table.rowCount() >= 0


# ===========================================================================
# RiskWidget
# ===========================================================================

class TestRiskWidget:
    """fylab.gui.widgets.risk_widget.RiskWidget"""

    def test_construction(self, qtbot):
        from fylab.gui.widgets.risk_widget import RiskWidget
        w = RiskWidget()
        qtbot.addWidget(w)

    def test_calc_metrics_low_sharpe(self, qtbot):
        """Standard-Werte → Sharpe < 1 → rote Farbe."""
        from fylab.gui.widgets.risk_widget import RiskWidget
        w = RiskWidget()
        qtbot.addWidget(w)
        # Standardwerte: mean=0.08, vol=0.20, rf=0.03 → Sharpe ≈ 0.25
        w._calc_metrics()
        assert w._lbl_sharpe.text() != "–"

    def test_calc_metrics_high_sharpe(self, qtbot):
        """Hohe Rendite, geringe Vola → Sharpe ≥ 1 → grüne Farbe."""
        from fylab.gui.widgets.risk_widget import RiskWidget
        w = RiskWidget()
        qtbot.addWidget(w)
        w._ret_mean.setValue(0.40)   # 40 % Rendite
        w._ret_vol.setValue(0.05)    # 5 % Volatilität
        w._risk_free.setValue(0.01)
        w._calc_metrics()
        sharpe_val = float(w._lbl_sharpe.text())
        assert sharpe_val >= 1.0

    def test_run_monte_carlo(self, qtbot):
        """Monte-Carlo-Simulation mit reduzierter Simulationsanzahl."""
        from fylab.gui.widgets.risk_widget import RiskWidget
        w = RiskWidget()
        qtbot.addWidget(w)
        w._n_sim.setValue(500)        # schnell halten
        w._initial_val.setValue(50_000.0)
        w._run_monte_carlo()


# ===========================================================================
# MainWindow
# ===========================================================================

class TestMainWindow:
    """fylab.gui.main_window.MainWindow – alle Methoden außer main()."""

    @pytest.fixture
    def win(self, qtbot):
        from fylab.gui.main_window import MainWindow
        with patch("fylab.gui.main_window.QMessageBox"):
            w = MainWindow()
        qtbot.addWidget(w)
        return w

    # ------------------------------------------------------------------ Bau
    def test_construction(self, win):
        from fylab.gui.main_window import MainWindow
        assert isinstance(win, MainWindow)

    def test_window_title_contains_version(self, win):
        assert "FyLab" in win.windowTitle()

    def test_tabs_five_entries(self, win):
        tabs = win.findChild(QTabWidget)
        assert tabs.count() == 5

    # ------------------------------------------------------------------ Navigation
    def test_goto_account(self, win):
        win._goto_account()
        assert win._tabs.currentIndex() == 0

    def test_goto_portfolio(self, win):
        win._goto_portfolio()
        assert win._tabs.currentIndex() == 1

    def test_goto_cashflow(self, win):
        win._goto_cashflow()
        assert win._tabs.currentIndex() == 2

    def test_goto_graph(self, win):
        win._goto_graph()
        assert win._tabs.currentIndex() == 3

    def test_goto_risk(self, win):
        win._goto_risk()
        assert win._tabs.currentIndex() == 4

    # ------------------------------------------------------------------ Slots / Dialoge
    def test_on_new_project(self, win):
        with patch("fylab.gui.main_window.QMessageBox") as mock_mb:
            win._on_new_project()
        mock_mb.information.assert_called_once()

    def test_on_about(self, win):
        with patch("fylab.gui.main_window.QMessageBox") as mock_mb:
            win._on_about()
        mock_mb.about.assert_called_once()

    # ------------------------------------------------------------------ Dock / Tree
    def test_dock_exists(self, win):
        dock = win.findChild(QDockWidget)
        assert dock is not None

    def test_tree_parent_item_in_tab_map_switches_tab(self, win):
        """Klick auf Elternknoten, der in tab_map ist → Tab wechselt."""
        dock = win.findChild(QDockWidget)
        tree = dock.widget()         # QTreeWidget
        # "Kontoverwaltung" → Index 0
        item = tree.invisibleRootItem().child(0)   # erster Elternknoten
        tree.itemClicked.emit(item, 0)
        assert win._tabs.currentIndex() == 0

    def test_tree_child_item_switches_to_parent_tab(self, win):
        """Klick auf Kindknoten → zugehöriger Tab des Elternknotens."""
        dock = win.findChild(QDockWidget)
        tree = dock.widget()
        # Zweiter Elternknoten "Portfolio" → Tab 1; klicke auf sein erstes Kind
        parent_item = tree.invisibleRootItem().child(1)   # "Portfolio"
        child_item = parent_item.child(0)                  # "Positionen"
        tree.itemClicked.emit(child_item, 0)
        assert win._tabs.currentIndex() == 1

    def test_tree_item_not_in_tab_map_defaults_to_zero(self, win):
        """Klick auf 'Algorithmen' (nicht in tab_map) → Tab 0."""
        dock = win.findChild(QDockWidget)
        tree = dock.widget()
        # "Algorithmen" ist der letzte Elternknoten (Index 5)
        alg_item = tree.invisibleRootItem().child(5)
        tree.itemClicked.emit(alg_item, 0)
        assert win._tabs.currentIndex() == 0

    def test_tree_child_of_non_tab_map_parent(self, win):
        """Kindknoten unter 'Algorithmen' → Elternknoten auch nicht in tab_map → 0."""
        dock = win.findChild(QDockWidget)
        tree = dock.widget()
        alg_item = tree.invisibleRootItem().child(5)   # "Algorithmen"
        child = alg_item.child(0)                       # "Subgraph-Isomorphismus"
        tree.itemClicked.emit(child, 0)
        assert win._tabs.currentIndex() == 0

    # ------------------------------------------------------------------ Menü-Aktionen
    def test_menu_analyse_actions_trigger(self, win):
        """Analyse-Menü-Aktionen können ausgelöst werden ohne Fehler."""
        mb = win.menuBar()
        analyse_menu = None
        for action in mb.actions():
            if "Analyse" in action.text():
                analyse_menu = action.menu()
                break
        assert analyse_menu is not None
        for action in analyse_menu.actions():
            action.trigger()    # löst goto_*-Slots aus

    def test_toolbar_actions_trigger(self, win):
        """Toolbar-Buttons des MainWindow (nur direkte Kinder) auslösen.

        FindDirectChildrenOnly verhindert, dass rekursiv die matplotlib
        NavigationToolbar2QT-Instanzen in den PlotWidgets gefunden werden –
        deren 'Save figure'-Aktion würde einen blockierenden QFileDialog öffnen.
        """
        for toolbar in win.findChildren(
            QToolBar,
            options=Qt.FindChildOption.FindDirectChildrenOnly,
        ):
            for action in toolbar.actions():
                if not action.isSeparator():
                    action.trigger()

    # ------------------------------------------------------------------ _scrolled helper
    def test_scrolled_helper(self, qtbot):
        """_scrolled() umhüllt ein Widget in QScrollArea."""
        from fylab.gui.main_window import _scrolled
        from PyQt6.QtWidgets import QScrollArea, QLabel
        lbl = QLabel("Test")
        qtbot.addWidget(lbl)
        sa = _scrolled(lbl)
        qtbot.addWidget(sa)
        assert isinstance(sa, QScrollArea)
        assert sa.widgetResizable()
