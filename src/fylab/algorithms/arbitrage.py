"""
fylab.algorithms.arbitrage
===========================
Arbitrage-Erkennung im Währungsgraphen via Bellman-Ford.

Problemstellung
---------------
Gegeben eine Menge von Währungen und Wechselkursen r(i→j).
Prüfe ob ein Kreislauf i₀→i₁→...→iₖ→i₀ existiert mit:
    r(i₀→i₁) · r(i₁→i₂) · ... · r(iₖ→i₀) > 1

Das bedeutet: man kann durch Tauschen von Währung mit einem positiven
Gewinn zurückkehren (Arbitrage-Möglichkeit).

Reduktion auf negativen Zyklus
-------------------------------
Logarithmische Transformation: w(i→j) = -log(r(i→j))
Ein Zyklus mit Produkt > 1 entspricht einem negativen Zyklus im
transformierten Graphen.

ARBITRAGE_DETECT ≤_p NEGATIVE_CYCLE ≤_p BELLMAN_FORD

Algorithmus: Bellman-Ford
Komplexität: O(V·E)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from fylab.algorithms.subgraph_finance import subgraph_contains


@dataclass
class ArbitrageResult:
    """Ergebnis der Arbitrage-Erkennung."""
    has_arbitrage: bool
    cycle: list[str]       # Währungszyklus (leer falls keine Arbitrage)
    profit_factor: float   # Gewinnmultiplikator (>1 = Arbitrage)
    cycle_patterns: list = field(default_factory=list)  # list[CyclePatternResult]

    def __str__(self) -> str:
        if self.has_arbitrage:
            cycle_str = " → ".join(self.cycle)
            return f"Arbitrage: {cycle_str}  (Faktor: {self.profit_factor:.4f}x)"
        return "Keine Arbitrage-Möglichkeit gefunden."


# ---------------------------------------------------------------------------
# Subgraph-basierte strukturelle Zykluserkennung
# ---------------------------------------------------------------------------
# Theoretische Einordnung:
#   ARBITRAGE ≤_p NEG_CYCLE ≤_p BELLMAN_FORD
#   Notwendige Bedingung: CYCLE_EXISTS ≤_p SUBGRAPH_ISO
#
# Bellman-Ford prüft Kantengewichte, aber setzt voraus, dass Zyklen im
# Konnektivitätsgraphen überhaupt existieren. Der Subgraph Algorithmus
# erledigt diese strukturelle Vorprüfung in O(n³) – optimal für diesen Schritt.
# ---------------------------------------------------------------------------

class CyclePattern(Enum):
    """Strukturelle k-Zyklusmuster im Währungsgraphen (Subgraph-Referenzmatrizen)."""
    CYCLE_2 = "2-Zyklus (direkter Gegenhandel)"
    CYCLE_3 = "3-Zyklus (Dreieck-Arbitrage)"
    CYCLE_4 = "4-Zyklus (Viereck-Arbitrage)"
    CYCLE_5 = "5-Zyklus (Fünfeck-Arbitrage)"


#: Referenz-Adjazenzmatrizen gerichteter k-Zyklen
#: (analog PATTERN_MATRICES in subgraph_finance.py)
CYCLE_PATTERN_MATRICES: dict[CyclePattern, np.ndarray] = {
    CyclePattern.CYCLE_2: np.array(
        [[0, 1], [1, 0]], dtype=int
    ),
    CyclePattern.CYCLE_3: np.array(
        [[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=int
    ),
    CyclePattern.CYCLE_4: np.array(
        [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0]], dtype=int
    ),
    CyclePattern.CYCLE_5: np.array(
        [[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0],
         [0, 0, 0, 0, 1], [1, 0, 0, 0, 0]], dtype=int
    ),
}


@dataclass
class CyclePatternResult:
    """Ergebnis einer Subgraph-basierten Zyklus-Strukturprüfung."""
    pattern: CyclePattern
    detected: bool
    decision: str


def detect_cycle_patterns(
    currencies: list[str],
    exchange_rates: dict[tuple[str, str], float],
) -> list[CyclePatternResult]:
    """
    Prüft den Währungsgraphen mittels Subgraph Algorithmus auf strukturelle k-Zyklen.

    Notwendige Bedingung für Arbitrage: der Konnektivitätsgraph muss mindestens
    einen gerichteten Zyklus enthalten. Diese strukturelle Vorprüfung (O(n³))
    ist bei azyklischen Graphen schneller als Bellman-Ford (O(V·E)).

    CYCLE_EXISTS ≤_p SUBGRAPH_ISO  → optimale Laufzeit für reine Strukturprüfung

    Parameters
    ----------
    currencies : Währungssymbole
    exchange_rates : {(von, nach): kurs}

    Returns
    -------
    list[CyclePatternResult] – für k = 2, 3, 4, 5
    """
    n = len(currencies)
    idx = {c: i for i, c in enumerate(currencies)}

    # Binäre Adjazenzmatrix des Konnektivitätsgraphen (1 wenn Kurs vorhanden)
    G_matrix = np.zeros((n, n), dtype=int)
    for (src, dst) in exchange_rates:
        if src in idx and dst in idx:
            G_matrix[idx[src]][idx[dst]] = 1

    results: list[CyclePatternResult] = []
    for pattern, R in CYCLE_PATTERN_MATRICES.items():
        if R.shape[0] > n:
            results.append(CyclePatternResult(
                pattern=pattern, detected=False, decision="graph_too_small"
            ))
            continue
        detected, decision = subgraph_contains(R, G_matrix)
        results.append(CyclePatternResult(pattern=pattern, detected=detected, decision=decision))

    return results


def detect_arbitrage(
    currencies: list[str],
    exchange_rates: dict[tuple[str, str], float],
) -> ArbitrageResult:
    """
    Erkennt Arbitrage im Währungsgraphen – zweistufiger Algorithmus:

    Stufe 1 – Subgraph-ISO-Vorprüfung (O(n³)):
        Prüft ob irgendein k-Zyklus strukturell im Konnektivitätsgraphen
        enthalten ist. Ist der Graph azyklisch, kann es keine Arbitrage geben
        → sofortige Rückgabe ohne Bellman-Ford.
        CYCLE_EXISTS ≤_p SUBGRAPH_ISO

    Stufe 2 – Bellman-Ford (O(V·E)):
        Exakte Erkennung negativer Zyklen im logarithmisch transformierten
        Gewichtsgraphen. Nur ausgeführt wenn Stufe 1 Zyklen gefunden hat.
        ARBITRAGE ≤_p NEG_CYCLE ≤_p BELLMAN_FORD

    Parameters
    ----------
    currencies : Liste der Währungssymbole
    exchange_rates : {(von, nach): kurs}

    Returns
    -------
    ArbitrageResult
    """
    # --- Stufe 1: Subgraph-Vorprüfung (O(n³)) ---
    # Mindestens ein gerichteter k-Zyklus muss strukturell existieren,
    # sonst ist Bellman-Ford unnötig (azyklischer Graph → keine Arbitrage).
    cycle_checks = detect_cycle_patterns(currencies, exchange_rates)
    if not any(r.detected for r in cycle_checks):
        return ArbitrageResult(
            has_arbitrage=False, cycle=[], profit_factor=1.0,
            cycle_patterns=cycle_checks,
        )

    # --- Stufe 2: Bellman-Ford (O(V·E)) ---
    # Logarithmische Transformation: w(u→v) = -log(rate) → negativer Zyklus = Arbitrage
    edges: list[tuple[str, str, float]] = [
        (src, dst, -math.log(rate))
        for (src, dst), rate in exchange_rates.items()
        if rate > 0
    ]

    dist = {c: 0.0 for c in currencies}
    pred: dict[str, str | None] = {c: None for c in currencies}

    n = len(currencies)
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist.get(u, 0.0) + w < dist.get(v, 0.0) - 1e-10:
                dist[v] = dist[u] + w
                pred[v] = u

    # n-te Relaxation: negativen Zyklus detektieren
    cycle_node = None
    for u, v, w in edges:
        if dist.get(u, 0.0) + w < dist.get(v, 0.0) - 1e-10:
            cycle_node = v
            break

    if cycle_node is None:
        return ArbitrageResult(
            has_arbitrage=False, cycle=[], profit_factor=1.0,
            cycle_patterns=cycle_checks,
        )

    # Zyklus rekonstruieren
    node = cycle_node
    for _ in range(n):
        node = pred[node]  # type: ignore[assignment]
    start = node
    cycle: list[str] = [start]
    node = pred[start]  # type: ignore[assignment]
    while node != start:
        cycle.append(node)
        node = pred[node]  # type: ignore[assignment]
    cycle.append(start)
    cycle.reverse()

    # Gewinnfaktor ermitteln
    profit_factor = 1.0
    for i in range(len(cycle) - 1):
        key = (cycle[i], cycle[i + 1])
        if key in exchange_rates:
            profit_factor *= exchange_rates[key]

    return ArbitrageResult(
        has_arbitrage=True, cycle=cycle, profit_factor=profit_factor,
        cycle_patterns=cycle_checks,
    )
