"""
fylab.gui.main_window
======================
FyLab Hauptfenster – Finanzlabor

Layout
------
┌──────────────────────────────────────────────────────────────┐
│ Menüleiste + Werkzeugleiste                                  │
├──────────────┬───────────────────────────────────────────────┤
│              │  Tab-Bereich                                  │
│  Übersicht   │   • Konto / Buchungen                         │
│  (Dock)      │   • Portfolio / Depot                         │
│              │   • Cashflow-Planung                          │
│              │   • Graphanalyse (Betrug, Arbitrage)          │
│              │   • Risikoanalyse (VaR, Monte-Carlo)          │
├──────────────┴───────────────────────────────────────────────┤
│ Statusleiste                                                 │
└──────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget,
    QVBoxLayout, QStatusBar, QTabWidget, QLabel, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QFont

from fylab.gui.widgets.account_widget import AccountWidget
from fylab.gui.widgets.portfolio_widget import PortfolioWidget
from fylab.gui.widgets.cashflow_widget import CashflowWidget
from fylab.gui.widgets.graph_widget import GraphWidget
from fylab.gui.widgets.risk_widget import RiskWidget
from fylab import __version__ as _version, __author__ as _author


def _scrolled(widget: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidget(widget)
    sa.setWidgetResizable(True)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    return sa


class MainWindow(QMainWindow):
    """FyLab-Hauptfenster."""

    APP_TITLE = f"FyLab  {_version}  –  Finanzlabor"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.APP_TITLE)

        self._build_menus()
        self._build_toolbars()
        self._build_central()
        self._build_docks()
        self._build_statusbar()

        self.showMaximized()

    # ------------------------------------------------------------------
    # UI-Aufbau
    # ------------------------------------------------------------------

    def _build_menus(self) -> None:
        mb = self.menuBar()

        # Datei
        file_menu = mb.addMenu("&Datei")
        act_new = QAction("&Neues Projekt", self, shortcut="Ctrl+N")
        act_new.triggered.connect(self._on_new_project)
        act_exit = QAction("&Beenden", self, shortcut="Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_new)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        # Analyse
        analyse_menu = mb.addMenu("&Analyse")
        for label, slot in [
            ("Betrugserkennung starten",  self._goto_graph),
            ("Arbitrage-Analyse",         self._goto_graph),
            ("Risiko berechnen",          self._goto_risk),
            ("Effizienzgrenze",           self._goto_portfolio),
        ]:
            act = QAction(label, self)
            act.triggered.connect(slot)
            analyse_menu.addAction(act)

        # Hilfe
        help_menu = mb.addMenu("&Hilfe")
        act_about = QAction("Über FyLab", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    def _build_toolbars(self) -> None:
        tb = self.addToolBar("Navigation")
        tb.setMovable(False)
        for label, slot, tip in [
            ("Konto",       self._goto_account,   "Kontoverwaltung"),
            ("Portfolio",   self._goto_portfolio, "Depot / Portfolio"),
            ("Cashflow",    self._goto_cashflow,  "Cashflow-Planung"),
            ("Graphanalyse",self._goto_graph,     "Betrugserkennung & Arbitrage"),
            ("Risiko",      self._goto_risk,      "VaR & Monte-Carlo"),
        ]:
            act = QAction(label, self)
            act.setStatusTip(tip)
            act.triggered.connect(slot)
            tb.addAction(act)

    def _build_central(self) -> None:
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(False)
        self._tabs.setMovable(True)

        self._account_widget   = AccountWidget()
        self._portfolio_widget = PortfolioWidget()
        self._cashflow_widget  = CashflowWidget()
        self._graph_widget     = GraphWidget()
        self._risk_widget      = RiskWidget()

        self._tabs.addTab(_scrolled(self._account_widget),   "Konto")
        self._tabs.addTab(_scrolled(self._portfolio_widget), "Portfolio")
        self._tabs.addTab(_scrolled(self._cashflow_widget),  "Cashflow")
        self._tabs.addTab(_scrolled(self._graph_widget),     "Graphanalyse")
        self._tabs.addTab(_scrolled(self._risk_widget),      "Risikoanalyse")

        self.setCentralWidget(self._tabs)

    def _build_docks(self) -> None:
        dock = QDockWidget("Module", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)

        tree = QTreeWidget()
        tree.setHeaderLabel("FyLab-Module")
        tree.setColumnCount(1)

        items = {
            "Kontoverwaltung": ["Buchungen", "Kategorien", "Monatsübersicht"],
            "Portfolio": ["Positionen", "Allokation", "Effizienzgrenze", "MST"],
            "Cashflow-Planung": ["Posten", "Jahresplan", "Prognose"],
            "Graphanalyse": ["Betrugserkennung", "Arbitrage", "Schuldenausgleich"],
            "Risikoanalyse": ["VaR / CVaR", "Monte-Carlo", "Kennzahlen"],
            "Algorithmen": [
                "Subgraph-Isomorphismus",
                "Bellman-Ford (Arbitrage)",
                "Kruskal MST (Diversifikation)",
                "Edmonds-Karp MaxFlow",
                "Markowitz Optimierung",
            ],
        }

        tab_map = {
            "Kontoverwaltung": 0,
            "Portfolio": 1,
            "Cashflow-Planung": 2,
            "Graphanalyse": 3,
            "Risikoanalyse": 4,
        }

        for parent_label, children in items.items():
            parent_item = QTreeWidgetItem(tree, [parent_label])
            for child in children:
                QTreeWidgetItem(parent_item, [child])

        tree.expandAll()
        tree.itemClicked.connect(
            lambda item, _col: self._tabs.setCurrentIndex(
                tab_map.get(item.text(0), tab_map.get(item.parent().text(0) if item.parent() else "", 0))
            )
        )

        dock.setWidget(tree)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        sb.showMessage(f"FyLab {_version}  –  {_author}  |  Bereit")
        version_lbl = QLabel(f"v{_version}")
        sb.addPermanentWidget(version_lbl)
        self.setStatusBar(sb)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _goto_account(self) -> None:
        self._tabs.setCurrentIndex(0)

    def _goto_portfolio(self) -> None:
        self._tabs.setCurrentIndex(1)

    def _goto_cashflow(self) -> None:
        self._tabs.setCurrentIndex(2)

    def _goto_graph(self) -> None:
        self._tabs.setCurrentIndex(3)

    def _goto_risk(self) -> None:
        self._tabs.setCurrentIndex(4)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_new_project(self) -> None:
        QMessageBox.information(
            self, "Neues Projekt",
            "Datei-Import (CSV/JSON) wird in Version 1.1 implementiert."
        )

    @pyqtSlot()
    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "Über FyLab",
            f"<b>FyLab {_version}</b><br>"
            f"Finanzlabor – Portfolio, Cashflow, Graphanalyse<br><br>"
            f"Algorithmen: Subgraph-Isomorphismus, Bellman-Ford,<br>"
            f"Kruskal MST, Edmonds-Karp MaxFlow, Markowitz-Optimierung<br><br>"
            f"Autor: {_author}<br>"
            f"Technologie: Python · PyQt6 · NumPy · SciPy · Matplotlib",
        )


def main() -> None:  # pragma: no cover
    app = QApplication(sys.argv)
    app.setApplicationName("FyLab")
    app.setOrganizationName("Stephan Epp")
    app.setStyle("Fusion")

    # Modernes dunkles Farbschema
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    dark = QColor(45, 45, 48)
    mid = QColor(62, 62, 66)
    light = QColor(210, 210, 210)
    highlight = QColor(0, 122, 204)
    palette.setColor(QPalette.ColorRole.Window, dark)
    palette.setColor(QPalette.ColorRole.WindowText, light)
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, mid)
    palette.setColor(QPalette.ColorRole.ToolTipBase, dark)
    palette.setColor(QPalette.ColorRole.ToolTipText, light)
    palette.setColor(QPalette.ColorRole.Text, light)
    palette.setColor(QPalette.ColorRole.Button, mid)
    palette.setColor(QPalette.ColorRole.ButtonText, light)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
