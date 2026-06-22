"""
fylab.gui.widgets.graph_widget
================================
Graphbasierte Finanzanalyse: Betrugserkennung, Arbitrage, Schuldenausgleich.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox,
)
from PyQt6.QtGui import QColor

from fylab.algorithms.subgraph_finance import (
    build_transaction_graph, detect_fraud_patterns, FraudPattern
)
from fylab.algorithms.arbitrage import detect_arbitrage
from fylab.algorithms.max_flow import simplify_debts
from fylab.visualization.graph_viz import plot_transaction_graph
from fylab.gui.widgets.plot_widget import PlotWidget, ScrollableTabWidget


def _demo_transactions() -> list[tuple[str, str, float]]:
    """Beispiel-Transaktionen mit verstecktem Wash-Trading."""
    return [
        ("Alice",  "Bob",    1500.0),
        ("Bob",    "Carol",   800.0),
        ("Carol",  "Alice",   900.0),   # Kreis: Wash-Trading
        ("Alice",  "Dave",    200.0),
        ("Alice",  "Eve",     150.0),
        ("Alice",  "Frank",   300.0),
        ("Alice",  "Grace",   100.0),   # Smurfing: Stern von Alice
        ("Dave",   "Heidi",   180.0),
        ("Heidi",  "Ivan",    160.0),
        ("Ivan",   "Judy",    140.0),   # Layering: Kette
    ]


def _demo_debts() -> list[tuple[str, str, float]]:
    return [
        ("Alice", "Bob",   30.0),
        ("Alice", "Carol", 20.0),
        ("Bob",   "Carol", 10.0),
        ("Carol", "Dave",  40.0),
        ("Dave",  "Alice", 25.0),
    ]


class GraphWidget(QWidget):
    """Graphanalyse-Widget: Betrug, Arbitrage, Schuldenausgleich."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        tabs = ScrollableTabWidget()
        layout.addWidget(tabs)

        # --- Tab 1: Betrugserkennung ---
        tab_fraud = QWidget()
        fl = QVBoxLayout(tab_fraud)
        fl.addWidget(QLabel(
            "<b>Subgraph-Isomorphismus</b>: Erkennt Betrugsmuster (Wash-Trading, "
            "Smurfing, Layering) als Subgraphen im Transaktionsnetzwerk."
        ))
        btn_fraud = QPushButton("Betrugsmuster analysieren")
        btn_fraud.clicked.connect(self._run_fraud_detection)
        fl.addWidget(btn_fraud)

        self._fraud_result = QTextEdit()
        self._fraud_result.setReadOnly(True)
        self._fraud_result.setMaximumHeight(120)
        fl.addWidget(self._fraud_result)

        self._plot_fraud = PlotWidget()
        fl.addWidget(self._plot_fraud)
        tabs.addTab(tab_fraud, "Betrugserkennung")

        # --- Tab 2: Arbitrage ---
        tab_arb = QWidget()
        al = QVBoxLayout(tab_arb)
        al.addWidget(QLabel(
            "<b>Bellman-Ford</b>: Negativen Zyklus im Wechselkursgraphen suchen. "
            "Arbitrage = Produkt der Kurse auf einem Zyklus > 1."
        ))
        btn_arb = QPushButton("Arbitrage-Analyse starten")
        btn_arb.clicked.connect(self._run_arbitrage)
        al.addWidget(btn_arb)
        self._arb_result = QTextEdit()
        self._arb_result.setReadOnly(True)
        al.addWidget(self._arb_result)
        tabs.addTab(tab_arb, "Arbitrage")

        # --- Tab 3: Schuldenausgleich ---
        tab_debt = QWidget()
        dl = QVBoxLayout(tab_debt)
        dl.addWidget(QLabel(
            "<b>Greedy Max-Flow Reduktion</b>: Minimiert Transaktionen "
            "für Schuldenausgleich durch Nettobalanzierung."
        ))
        btn_debt = QPushButton("Schulden vereinfachen")
        btn_debt.clicked.connect(self._run_debt_simplify)
        dl.addWidget(btn_debt)

        self._debt_table = QTableWidget()
        self._debt_table.setColumnCount(3)
        self._debt_table.setHorizontalHeaderLabels(["Zahler", "Empfänger", "Betrag (€)"])
        self._debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._debt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        dl.addWidget(self._debt_table)
        tabs.addTab(tab_debt, "Schuldenausgleich")

    def _run_fraud_detection(self) -> None:
        txns = _demo_transactions()
        g = build_transaction_graph(txns)
        results = detect_fraud_patterns(g)

        lines = []
        for r in results:
            status = "🔴 ERKANNT" if r.detected else "✅ nicht gefunden"
            lines.append(f"{status}: {r.pattern.value}")
        self._fraud_result.setText("\n".join(lines))

        fig = plot_transaction_graph(g, results, "Transaktionsnetzwerk mit Betrugsmarkierung")
        self._plot_fraud.set_figure(fig)

    def _run_arbitrage(self) -> None:
        currencies = ["EUR", "USD", "GBP", "JPY", "CHF"]
        # Realistische Kurse + eine künstliche Arbitrage-Möglichkeit
        rates = {
            ("EUR", "USD"): 1.085, ("USD", "EUR"): 0.9217,
            ("EUR", "GBP"): 0.857, ("GBP", "EUR"): 1.1669,
            ("EUR", "JPY"): 163.2, ("JPY", "EUR"): 0.00613,
            ("EUR", "CHF"): 0.952, ("CHF", "EUR"): 1.0504,
            ("USD", "GBP"): 0.789, ("GBP", "USD"): 1.267,
            ("USD", "JPY"): 150.4, ("JPY", "USD"): 0.00665,
            ("GBP", "JPY"): 190.6, ("JPY", "GBP"): 0.00525,
            # Künstliche Arbitrage: EUR->USD->GBP->EUR mit Faktor > 1
            ("USD", "CHF"): 0.899, ("CHF", "USD"): 1.115,
        }
        result = detect_arbitrage(currencies, rates)
        self._arb_result.setText(str(result))

    def _run_debt_simplify(self) -> None:
        debts = _demo_debts()
        transactions = simplify_debts(debts)
        self._debt_table.setRowCount(len(transactions))
        for row, txn in enumerate(transactions):
            self._debt_table.setItem(row, 0, QTableWidgetItem(txn.payer))
            self._debt_table.setItem(row, 1, QTableWidgetItem(txn.receiver))
            amt_item = QTableWidgetItem(f"{txn.amount:.2f}")
            amt_item.setForeground(QColor("#e74c3c"))
            self._debt_table.setItem(row, 2, amt_item)
