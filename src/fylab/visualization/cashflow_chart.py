"""
fylab.visualization.cashflow_chart
====================================
Cashflow-Wasserfall und Monatsübersicht.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from fylab.core.cashflow import CashflowPlan
from fylab.core.account import Account


def plot_cashflow_waterfall(plan: CashflowPlan, year: int) -> Figure:
    """Wasserfall-Diagramm des monatlichen Cashflows."""
    monthly = plan.monthly_cashflow(year)
    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    values = np.array([monthly.get(m, 0.0) for m in months])
    cumulative = np.cumsum(values)
    month_labels = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Monatlicher Netto-Cashflow
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]
    ax1.bar(month_labels, values, color=colors, edgecolor="white", linewidth=0.5)
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_ylabel("Netto-Cashflow (€)")
    ax1.set_title(f"Monatlicher Cashflow – {plan.name} ({year})")
    ax1.grid(True, axis="y", alpha=0.3)

    # Kumulierter Cashflow
    ax2.plot(month_labels, cumulative, marker="o", color="#3498db", linewidth=2)
    ax2.fill_between(range(12), cumulative, alpha=0.15, color="#3498db")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Kumulierter Cashflow (€)")
    ax2.set_xlabel("Monat")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_income_expense(account: Account) -> Figure:
    """Balkendiagramm: Einnahmen vs. Ausgaben pro Monat."""
    summary = account.monthly_summary()
    months = list(summary.keys())
    incomes = [summary[m]["income"] for m in months]
    expenses = [summary[m]["expense"] for m in months]

    x = np.arange(len(months))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width / 2, incomes, width, label="Einnahmen", color="#2ecc71")
    ax.bar(x + width / 2, expenses, width, label="Ausgaben", color="#e74c3c")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Betrag (€)")
    ax.set_title(f"Einnahmen & Ausgaben – {account.name}")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    return fig
