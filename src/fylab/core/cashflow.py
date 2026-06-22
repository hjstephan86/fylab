"""
fylab.core.cashflow
====================
Cashflow-Modellierung: Zahlungsströme, Budgetplanung, Prognose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List

import numpy as np


class Frequency(Enum):
    ONCE = "einmalig"
    DAILY = "täglich"
    WEEKLY = "wöchentlich"
    MONTHLY = "monatlich"
    QUARTERLY = "vierteljährlich"
    YEARLY = "jährlich"


@dataclass
class CashflowItem:
    """Geplante Zahlung mit Frequenz."""
    name: str
    amount: float        # positiv = Einnahme, negativ = Ausgabe
    start_date: date
    frequency: Frequency
    end_date: date | None = None

    def occurrences(self, from_date: date, to_date: date) -> List[date]:
        """Alle Zahlungszeitpunkte im angegebenen Zeitraum."""
        dates: List[date] = []
        current = self.start_date
        end = self.end_date or to_date

        deltas = {
            Frequency.ONCE: None,
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(weeks=1),
            Frequency.MONTHLY: None,   # speziell behandelt
            Frequency.QUARTERLY: None,
            Frequency.YEARLY: None,
        }

        if self.frequency == Frequency.ONCE:
            if from_date <= current <= to_date:
                dates.append(current)
            return dates

        while current <= min(end, to_date):
            if current >= from_date:
                dates.append(current)
            if self.frequency == Frequency.DAILY:
                current += timedelta(days=1)
            elif self.frequency == Frequency.WEEKLY:
                current += timedelta(weeks=1)
            elif self.frequency == Frequency.MONTHLY:
                month = current.month + 1
                year = current.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                day = min(current.day, [31,28+int((year%4==0 and year%100!=0)or year%400==0),
                          31,30,31,30,31,31,30,31,30,31][month-1])
                current = date(year, month, day)
            elif self.frequency == Frequency.QUARTERLY:
                month = current.month + 3
                year = current.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                current = date(year, month, current.day)
            elif self.frequency == Frequency.YEARLY:
                current = date(current.year + 1, current.month, current.day)
        return dates


@dataclass
class CashflowPlan:
    """Gesamter Cashflow-Plan aus mehreren Posten."""
    name: str
    items: List[CashflowItem] = field(default_factory=list)

    def monthly_cashflow(self, year: int) -> dict[str, float]:
        """Netto-Cashflow pro Monat für ein Jahr."""
        result: dict[str, float] = {}
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        for item in self.items:
            for occ in item.occurrences(start, end):
                key = occ.strftime("%Y-%m")
                result[key] = result.get(key, 0.0) + item.amount
        return dict(sorted(result.items()))

    def cumulative_cashflow(self, year: int) -> np.ndarray:
        """Kumulierter Cashflow über 12 Monate."""
        monthly = self.monthly_cashflow(year)
        months = [f"{year}-{m:02d}" for m in range(1, 13)]
        values = np.array([monthly.get(m, 0.0) for m in months])
        return np.cumsum(values)
