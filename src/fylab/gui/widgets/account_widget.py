"""
fylab.gui.widgets.account_widget
==================================
Konto-/Buchungs-Widget: Transaktionsliste, Kategoriefilter, Kontostand.
"""

from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QComboBox, QHeaderView, QGroupBox, QFormLayout,
    QDoubleSpinBox, QLineEdit, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from fylab.core.account import Account, AccountType, Transaction, TransactionCategory
from fylab.visualization.cashflow_chart import plot_income_expense
from fylab.gui.widgets.plot_widget import PlotWidget


def _demo_account() -> Account:
    """Erstellt ein Demo-Konto mit Beispieltransaktionen."""
    acc = Account("DE001", "Hauptkonto", AccountType.CHECKING, initial_balance=1500.0)
    entries = [
        (date(2026, 1, 1),   3200.0,  "Gehalt Januar",        TransactionCategory.INCOME),
        (date(2026, 1, 5),   -850.0,  "Miete",                TransactionCategory.EXPENSE),
        (date(2026, 1, 10),  -120.0,  "Lebensmittel",         TransactionCategory.EXPENSE),
        (date(2026, 1, 15),  -500.0,  "ETF-Sparplan",         TransactionCategory.INVESTMENT),
        (date(2026, 2, 1),   3200.0,  "Gehalt Februar",       TransactionCategory.INCOME),
        (date(2026, 2, 5),   -850.0,  "Miete",                TransactionCategory.EXPENSE),
        (date(2026, 2, 12),  -95.0,   "Strom & Gas",          TransactionCategory.EXPENSE),
        (date(2026, 2, 20),   150.0,  "Dividende SAP",        TransactionCategory.DIVIDEND),
        (date(2026, 3, 1),   3200.0,  "Gehalt März",          TransactionCategory.INCOME),
        (date(2026, 3, 5),   -850.0,  "Miete",                TransactionCategory.EXPENSE),
    ]
    for d, amt, desc, cat in entries:
        acc.add_transaction(Transaction(d, amt, desc, cat, acc.account_id))
    return acc


class AccountWidget(QWidget):
    """Konto-Übersicht mit Transaktionsliste und Monatschart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._account = _demo_account()
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Kopfzeile
        header = QHBoxLayout()
        self._lbl_name = QLabel()
        self._lbl_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._lbl_balance = QLabel()
        self._lbl_balance.setStyleSheet("font-size: 15px; color: #27ae60;")
        header.addWidget(self._lbl_name)
        header.addStretch()
        header.addWidget(QLabel("Kontostand:"))
        header.addWidget(self._lbl_balance)
        layout.addLayout(header)

        # Kategoriefilter + Neue Buchung
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self._combo_cat = QComboBox()
        self._combo_cat.addItem("Alle")
        for cat in TransactionCategory:
            self._combo_cat.addItem(cat.value, cat)
        self._combo_cat.currentIndexChanged.connect(self._refresh_table)
        filter_row.addWidget(self._combo_cat)
        filter_row.addStretch()
        btn_add = QPushButton("+ Buchung")
        btn_add.clicked.connect(self._show_add_dialog)
        filter_row.addWidget(btn_add)
        layout.addLayout(filter_row)

        # Transaktions-Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Datum", "Beschreibung", "Kategorie", "Betrag (€)", "Saldo (€)"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # Chart
        self._plot = PlotWidget()
        self._plot.setMinimumHeight(220)
        layout.addWidget(self._plot)

    def _refresh(self) -> None:
        self._lbl_name.setText(f"{self._account.account_type.value}: {self._account.name}")
        balance = self._account.balance
        color = "#27ae60" if balance >= 0 else "#e74c3c"
        self._lbl_balance.setStyleSheet(f"font-size: 15px; color: {color};")
        self._lbl_balance.setText(f"{balance:,.2f} {self._account.currency}")
        self._refresh_table()
        fig = plot_income_expense(self._account)
        self._plot.set_figure(fig)

    def _refresh_table(self) -> None:
        idx = self._combo_cat.currentIndex()
        if idx == 0:
            txns = self._account.transactions
        else:
            cat = self._combo_cat.currentData()
            txns = self._account.transactions_by_category(cat)

        self._table.setRowCount(len(txns))
        running = self._account.initial_balance
        all_txns = sorted(self._account.transactions, key=lambda t: t.date)

        for row, txn in enumerate(sorted(txns, key=lambda t: t.date)):
            # Laufender Saldo nur bei ungefiltert sinnvoll
            self._table.setItem(row, 0, QTableWidgetItem(str(txn.date)))
            self._table.setItem(row, 1, QTableWidgetItem(txn.description))
            self._table.setItem(row, 2, QTableWidgetItem(txn.category.value))

            amt_item = QTableWidgetItem(f"{txn.amount:+.2f}")
            color = QColor("#c8f7c5") if txn.amount > 0 else QColor("#fad7d7")
            amt_item.setBackground(color)
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 3, amt_item)
            self._table.setItem(row, 4, QTableWidgetItem("–"))

    def _show_add_dialog(self) -> None:
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Neue Buchung")
        form = QFormLayout(dlg)

        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(-1_000_000, 1_000_000)
        amount_spin.setDecimals(2)
        amount_spin.setSuffix(" €")
        desc_edit = QLineEdit()
        cat_combo = QComboBox()
        for cat in TransactionCategory:
            cat_combo.addItem(cat.value, cat)

        form.addRow("Datum:", date_edit)
        form.addRow("Betrag:", amount_spin)
        form.addRow("Beschreibung:", desc_edit)
        form.addRow("Kategorie:", cat_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            qd = date_edit.date()
            txn = Transaction(
                date=date(qd.year(), qd.month(), qd.day()),
                amount=amount_spin.value(),
                description=desc_edit.text() or "Buchung",
                category=cat_combo.currentData(),
                account_id=self._account.account_id,
            )
            self._account.add_transaction(txn)
            self._refresh()
