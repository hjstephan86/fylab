"""
fylab.core.currency
====================
Währungskonvertierung und Wechselkursverwaltung.
"""

from __future__ import annotations

from typing import Dict


class CurrencyConverter:
    """
    Einfacher Währungskonverter basierend auf einem Wechselkursgraph.

    Alle Kurse werden relativ zu EUR gespeichert (1 EUR = x Fremdwährung).
    Arbitrage-Erkennung erfolgt in fylab.algorithms.arbitrage.
    """

    def __init__(self) -> None:
        # Standardkurse (Stand: statisch für Demo)
        self._rates: Dict[str, float] = {
            "EUR": 1.0,
            "USD": 1.085,
            "GBP": 0.857,
            "JPY": 163.2,
            "CHF": 0.952,
            "CAD": 1.478,
            "AUD": 1.645,
            "CNY": 7.86,
            "BTC": 0.0000153,   # 1 EUR ≈ 0.0000153 BTC
        }

    def update_rate(self, currency: str, rate_vs_eur: float) -> None:
        """Aktualisiert den Wechselkurs einer Währung gegen EUR."""
        if rate_vs_eur <= 0:
            raise ValueError(f"Wechselkurs muss positiv sein, erhalten: {rate_vs_eur}")
        self._rates[currency.upper()] = rate_vs_eur

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Konvertiert einen Betrag zwischen zwei Währungen."""
        fc = from_currency.upper()
        tc = to_currency.upper()
        if fc not in self._rates:
            raise KeyError(f"Unbekannte Währung: {fc}")
        if tc not in self._rates:
            raise KeyError(f"Unbekannte Währung: {tc}")
        amount_in_eur = amount / self._rates[fc]
        return amount_in_eur * self._rates[tc]

    def rate(self, from_currency: str, to_currency: str) -> float:
        """Direkter Wechselkurs von from_currency zu to_currency."""
        return self.convert(1.0, from_currency, to_currency)

    @property
    def available_currencies(self) -> list[str]:
        return sorted(self._rates.keys())

    def rate_matrix(self) -> tuple[list[str], list[list[float]]]:
        """Vollständige Wechselkursmatrix für alle hinterlegten Währungen."""
        currencies = self.available_currencies
        n = len(currencies)
        matrix = [[self.rate(currencies[i], currencies[j]) for j in range(n)] for i in range(n)]
        return currencies, matrix
