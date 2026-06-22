"""
fylab.core.portfolio
=====================
Wertpapier-Portfolio: Assets, Positionen, Markowitz-Modell-Daten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np


class AssetClass(Enum):
    STOCK = "Aktie"
    BOND = "Anleihe"
    ETF = "ETF"
    CRYPTO = "Kryptowährung"
    REAL_ESTATE = "Immobilie"
    COMMODITY = "Rohstoff"
    CASH = "Liquidität"


@dataclass
class Asset:
    """Einzelnes Wertpapier."""
    symbol: str
    name: str
    asset_class: AssetClass
    currency: str = "EUR"

    def __hash__(self) -> int:
        return hash(self.symbol)


@dataclass
class Position:
    """Depotposition: Wertpapier + Menge + Einstiegspreis."""
    asset: Asset
    quantity: float
    avg_buy_price: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def book_value(self) -> float:
        return self.quantity * self.avg_buy_price

    @property
    def profit_loss(self) -> float:
        return self.market_value - self.book_value

    @property
    def profit_loss_pct(self) -> float:
        if self.book_value == 0:
            return 0.0
        return (self.profit_loss / self.book_value) * 100.0


@dataclass
class Portfolio:
    """Gesamtportfolio aus Positionen."""
    name: str
    positions: List[Position] = field(default_factory=list)

    @property
    def total_value(self) -> float:
        return sum(p.market_value for p in self.positions)

    @property
    def total_profit_loss(self) -> float:
        return sum(p.profit_loss for p in self.positions)

    def weight(self, symbol: str) -> float:
        """Portfoliogewicht einer Position."""
        total = self.total_value
        if total == 0:
            return 0.0
        for p in self.positions:
            if p.asset.symbol == symbol:
                return p.market_value / total
        return 0.0

    def weights_vector(self) -> np.ndarray:
        total = self.total_value
        if total == 0:
            return np.zeros(len(self.positions))
        return np.array([p.market_value / total for p in self.positions])

    def asset_class_allocation(self) -> Dict[str, float]:
        alloc: Dict[str, float] = {}
        total = self.total_value
        for p in self.positions:
            key = p.asset.asset_class.value
            alloc[key] = alloc.get(key, 0.0) + (p.market_value / total if total else 0.0)
        return alloc
