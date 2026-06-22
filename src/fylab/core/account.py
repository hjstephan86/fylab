"""
fylab.core.account
==================
Konto-, Buchungs- und Kategorisierungsmodell.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class AccountType(Enum):
    CHECKING = "Girokonto"
    SAVINGS = "Sparkonto"
    INVESTMENT = "Depot"
    CREDIT = "Kreditkonto"
    CASH = "Bargeld"


class TransactionCategory(Enum):
    INCOME = "Einnahme"
    EXPENSE = "Ausgabe"
    INVESTMENT = "Investition"
    TRANSFER = "Übertrag"
    TAX = "Steuer"
    DIVIDEND = "Dividende"
    INTEREST = "Zinsen"
    FEE = "Gebühr"


@dataclass
class Transaction:
    """Einzelne Finanztransaktion."""
    date: date
    amount: float          # positiv = Einnahme, negativ = Ausgabe
    description: str
    category: TransactionCategory
    account_id: str
    counter_party: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    def __repr__(self) -> str:
        sign = "+" if self.amount >= 0 else ""
        return f"Transaction({self.date}, {sign}{self.amount:.2f}€, {self.description!r})"


@dataclass
class Account:
    """Finanzkonto mit Buchungshistorie."""
    account_id: str
    name: str
    account_type: AccountType
    currency: str = "EUR"
    initial_balance: float = 0.0
    transactions: List[Transaction] = field(default_factory=list)

    @property
    def balance(self) -> float:
        return self.initial_balance + sum(t.amount for t in self.transactions)

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def transactions_by_category(self, category: TransactionCategory) -> List[Transaction]:
        return [t for t in self.transactions if t.category == category]

    def monthly_summary(self) -> dict[str, dict[str, float]]:
        """Gibt monatliche Ein-/Ausgaben als dict zurück: {YYYY-MM: {income, expense}}."""
        summary: dict[str, dict[str, float]] = {}
        for t in self.transactions:
            key = t.date.strftime("%Y-%m")
            if key not in summary:
                summary[key] = {"income": 0.0, "expense": 0.0}
            if t.amount > 0:
                summary[key]["income"] += t.amount
            else:
                summary[key]["expense"] += abs(t.amount)
        return dict(sorted(summary.items()))
