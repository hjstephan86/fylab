"""
fylab.gui.widgets.cashflow_widget
===================================
Cashflow-Planung: Einnahmen/Ausgaben planen und visualisieren.
"""

from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QSpinBox,
    QComboBox, QHeaderView, QDoubleSpinBox, QLineEdit,
    QTabWidget,
)
from PyQt6.QtCore import Qt

from fylab.core.cashflow import CashflowPlan, CashflowItem, Frequency
from fylab.visualization.cashflow_chart import plot_cashflow_waterfall
from fylab.gui.widgets.plot_widget import PlotWidget


def _demo_plan() -> CashflowPlan:
    plan = CashflowPlan("Haushaltsplan 2026")
    plan.items = [
        CashflowItem("Gehalt",          3200.0,   date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Miete",           -850.0,   date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Lebensmittel",    -400.0,   date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("ETF-Sparplan",    -500.0,   date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Jahresbonus",     3000.0,   date(2026, 6, 1),  Frequency.ONCE),
        CashflowItem("Kfz-Steuer",      -320.0,   date(2026, 3, 1),  Frequency.YEARLY),
        CashflowItem("Strom & Gas",     -110.0,   date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Netflix & Co.",   -35.0,    date(2026, 1, 1),  Frequency.MONTHLY, date(2026, 12, 31)),
    ]
    return plan


class CashflowWidget(QWidget):
    """Cashflow-Planungs-Widget mit Tabelle und Wasserfall-Chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plan = _demo_plan()
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Kopfzeile
        header = QHBoxLayout()
        header.addWidget(QLabel("Cashflow-Planung"))
        header.addStretch()
        header.addWidget(QLabel("Jahr:"))
        self._year_spin = QSpinBox()
        self._year_spin.setRange(2020, 2040)
        self._year_spin.setValue(2026)
        self._year_spin.valueChanged.connect(self._refresh)
        header.addWidget(self._year_spin)
        btn_add = QPushButton("+ Posten")
        btn_add.clicked.connect(self._add_item)
        header.addWidget(btn_add)
        layout.addLayout(header)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Posten-Tabelle
        tab_table = QWidget()
        tl = QVBoxLayout(tab_table)
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Bezeichnung", "Betrag (€)", "Frequenz", "Von", "Bis"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        tl.addWidget(self._table)

        # Summenszeile
        self._lbl_summary = QLabel()
        tl.addWidget(self._lbl_summary)
        tabs.addTab(tab_table, "Posten")

        # Tab 2: Wasserfall-Chart
        tab_chart = QWidget()
        cl = QVBoxLayout(tab_chart)
        self._plot = PlotWidget()
        cl.addWidget(self._plot)
        tabs.addTab(tab_chart, "Cashflow-Chart")

    def _refresh(self) -> None:
        year = self._year_spin.value()
        self._table.setRowCount(len(self._plan.items))
        for row, item in enumerate(self._plan.items):
            self._table.setItem(row, 0, QTableWidgetItem(item.name))
            amt = QTableWidgetItem(f"{item.amount:+.2f}")
            from PyQt6.QtGui import QColor
            amt.setForeground(QColor("#27ae60") if item.amount > 0 else QColor("#e74c3c"))
            amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, amt)
            self._table.setItem(row, 2, QTableWidgetItem(item.frequency.value))
            self._table.setItem(row, 3, QTableWidgetItem(str(item.start_date)))
            self._table.setItem(row, 4, QTableWidgetItem(str(item.end_date or "–")))

        monthly = self._plan.monthly_cashflow(year)
        total = sum(monthly.values())
        color = "#27ae60" if total >= 0 else "#e74c3c"
        self._lbl_summary.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._lbl_summary.setText(f"Jahresnetto {year}: {total:+,.2f} €")

        fig = plot_cashflow_waterfall(self._plan, year)
        self._plot.set_figure(fig)

    def _add_item(self) -> None:
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QDateEdit
        from PyQt6.QtCore import QDate

        dlg = QDialog(self)
        dlg.setWindowTitle("Neuer Cashflow-Posten")
        form = QFormLayout(dlg)

        name_edit = QLineEdit()
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(-1_000_000, 1_000_000)
        amount_spin.setDecimals(2)
        amount_spin.setSuffix(" €")
        freq_combo = QComboBox()
        for f in Frequency:
            freq_combo.addItem(f.value, f)
        start_edit = QDateEdit(QDate.currentDate())
        start_edit.setCalendarPopup(True)

        form.addRow("Bezeichnung:", name_edit)
        form.addRow("Betrag:", amount_spin)
        form.addRow("Frequenz:", freq_combo)
        form.addRow("Startdatum:", start_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            qd = start_edit.date()
            item = CashflowItem(
                name=name_edit.text() or "Posten",
                amount=amount_spin.value(),
                start_date=date(qd.year(), qd.month(), qd.day()),
                frequency=freq_combo.currentData(),
            )
            self._plan.items.append(item)
            self._refresh()
