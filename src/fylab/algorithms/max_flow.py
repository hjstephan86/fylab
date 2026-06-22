"""
fylab.algorithms.max_flow
==========================
Max-Flow für Cashflow-Optimierung und Schuldenausgleich.

Problemstellung Cashflow-Optimierung
--------------------------------------
Gegeben ein Netzwerk aus Konten (Knoten) und Zahlungsströmen (Kanten mit
Kapazität = maximaler Transferbetrag), finde den maximalen Zahlungsfluss
von einer Quelle (z.B. Einnahmekonto) zu einer Senke (z.B. Investmentkonto).

Algorithmus: Edmonds-Karp (BFS-basiertes Ford-Fulkerson)
Komplexität: O(V * E²)

Schuldenausgleich / Debt Simplification
-----------------------------------------
Problem: n Personen haben untereinander Schulden. Minimiere die Anzahl
der Transaktionen um alle Schulden zu begleichen.

Reduktion: Berechne Nettosaldo jeder Person. Maximierer (positiver Saldo)
transferieren direkt an Minimierer (negativer Saldo).
Komplexität: O(n log n) nach Reduktion.

Dieser Ansatz ist eine polynomielle Vereinfachung (nicht exakt optimal bzgl.
Minimierung der Transaktionsanzahl, was NP-hart ist – Reduktion aus Partition).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum

import numpy as np

from fylab.algorithms.subgraph_finance import subgraph_contains


@dataclass
class FlowResult:
    """Ergebnis der Max-Flow-Berechnung."""
    max_flow_value: float
    flow_dict: dict   # Kante -> Fluss

    def __str__(self) -> str:
        return f"Max-Flow = {self.max_flow_value:.2f}"


# Kapazitätsgraph: {knoten: {nachbar: kapazität}}
CapGraph = dict[str, dict[str, float]]


def _bfs_path(
    residual: CapGraph, source: str, sink: str, parent: dict[str, str | None]
) -> float:
    """BFS über Residualgraph – gibt Pfad-Fluss zurück (0 wenn kein Pfad)."""
    visited = {source}
    queue: deque[tuple[str, float]] = deque([(source, float("inf"))])
    while queue:
        node, flow = queue.popleft()
        for neighbor, cap in residual.get(node, {}).items():
            if neighbor not in visited and cap > 1e-10:
                visited.add(neighbor)
                parent[neighbor] = node
                new_flow = min(flow, cap)
                if neighbor == sink:
                    return new_flow
                queue.append((neighbor, new_flow))
    return 0.0


def compute_max_flow(
    graph: CapGraph,
    source: str,
    sink: str,
) -> FlowResult:
    """
    Berechnet den maximalen Geldfluss via Edmonds-Karp (BFS-Ford-Fulkerson).

    Parameters
    ----------
    graph : {knoten: {nachbar: kapazität}} – Gerichtetes Kapazitätsnetzwerk
    source : Quellknoten (z.B. Gehaltskonto)
    sink : Senkenknoten (z.B. Sparkonto)

    Returns
    -------
    FlowResult
    """
    # Residualgraph aufbauen
    residual: CapGraph = {}
    for u, neighbors in graph.items():
        for v, cap in neighbors.items():
            residual.setdefault(u, {})[v] = cap
            residual.setdefault(v, {}).setdefault(u, 0.0)

    flow_dict: dict[str, dict[str, float]] = {
        u: {v: 0.0 for v in neighbors} for u, neighbors in graph.items()
    }
    max_flow_val = 0.0

    while True:
        parent: dict[str, str | None] = {source: None}
        path_flow = _bfs_path(residual, source, sink, parent)
        if path_flow == 0.0:
            break
        max_flow_val += path_flow
        # Residualkapazitäten aktualisieren
        node: str = sink
        while node != source:
            prev = parent[node]  # type: ignore[assignment]
            residual[prev][node] -= path_flow
            residual[node][prev] = residual[node].get(prev, 0.0) + path_flow
            if prev in flow_dict and node in flow_dict.get(prev, {}):
                flow_dict[prev][node] += path_flow
            node = prev

    return FlowResult(max_flow_value=max_flow_val, flow_dict=flow_dict)


@dataclass
class DebtTransaction:
    """Vereinfachte Schulden-Transaktion."""
    payer: str
    receiver: str
    amount: float

    def __str__(self) -> str:
        return f"{self.payer} zahlt {self.amount:.2f}€ an {self.receiver}"


# ---------------------------------------------------------------------------
# Subgraph-basierte Schuldenstruktur-Analyse
# ---------------------------------------------------------------------------
# Bekannte Schuldenstrukturen werden als Subgraph-Muster kodiert und
# im Schuldengrafen gesucht. Dadurch wird die Art der Vereinfachung erklärbar.
#
# SCHULDEN_MUSTER ≤_p SUBGRAPH_ISO
#
# Erkannte Muster helfen, die optimale Vereinfachungsstrategie zu wählen:
# - Dreieck-Zyklus:  gegenseitige Schulden können durch Verrechnung minimiert werden
# - Hub-Schuldner:   eine Person schuldet vielen → Sammeltransaktion
# - Hub-Gläubiger:   viele schulden einer Person → direkte Auszahlung
# - Kette:           indirekte Weiterleitung (A→B→C→D) möglich
# ---------------------------------------------------------------------------

class DebtPattern(Enum):
    """Bekannte Schuldenstrukturen als Subgraph-Muster."""
    TRIANGLE_CYCLE = "Dreieck-Schuld (3-Zyklus)"
    HUB_DEBTOR     = "Zentralschuldner (Stern-Aus: einer schuldet vielen)"
    HUB_CREDITOR   = "Zentralgläubiger (Stern-Ein: viele schulden einem)"
    CHAIN          = "Schulden-Kette (4-Knoten)"


#: Referenz-Adjazenzmatrizen der Schuldenmuster
#: Kante A→B bedeutet: A schuldet B (Schuldner → Gläubiger)
DEBT_PATTERN_MATRICES: dict[DebtPattern, np.ndarray] = {
    DebtPattern.TRIANGLE_CYCLE: np.array(
        [[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=int
    ),
    DebtPattern.HUB_DEBTOR: np.array(
        [[0, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], dtype=int
    ),
    DebtPattern.HUB_CREDITOR: np.array(
        [[0, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]], dtype=int
    ),
    DebtPattern.CHAIN: np.array(
        [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0]], dtype=int
    ),
}


@dataclass
class DebtPatternResult:
    """Ergebnis einer Subgraph-basierten Schuldenmuster-Prüfung."""
    pattern: DebtPattern
    detected: bool
    decision: str

    def __str__(self) -> str:
        status = "erkannt" if self.detected else "nicht gefunden"
        return f"[{status}] {self.pattern.value}"


def detect_debt_patterns(
    debts: list[tuple[str, str, float]],
) -> list[DebtPatternResult]:
    """
    Prüft die Schuldenstruktur auf bekannte Muster via Subgraph Algorithmus.

    Der Schuldengraph wird als binäre Adjazenzmatrix kodiert:
    Kante A→B = 1 wenn A dem B schuldet. Der Subgraph Algorithmus prüft
    für jedes Referenzmuster ob es als Subgraph im Schuldengrafen enthalten ist.

    SCHULDEN_MUSTER ≤_p SUBGRAPH_ISO (optimale Laufzeit O(n³))

    Parameters
    ----------
    debts : list of (schuldner, gläubiger, betrag)

    Returns
    -------
    list[DebtPatternResult]
    """
    # Schulden → geordnete Knotenliste + binäre Adjazenzmatrix
    nodes: list[str] = []
    for debtor, creditor, _ in debts:
        if debtor not in nodes:
            nodes.append(debtor)
        if creditor not in nodes:
            nodes.append(creditor)
    n = len(nodes)
    idx = {p: i for i, p in enumerate(nodes)}
    G_matrix = np.zeros((n, n), dtype=int)
    for debtor, creditor, _ in debts:
        G_matrix[idx[debtor]][idx[creditor]] = 1

    results: list[DebtPatternResult] = []
    for pattern, R in DEBT_PATTERN_MATRICES.items():
        if R.shape[0] > n:
            results.append(DebtPatternResult(
                pattern=pattern, detected=False, decision="graph_too_small"
            ))
            continue
        detected, decision = subgraph_contains(R, G_matrix)
        results.append(DebtPatternResult(pattern=pattern, detected=detected, decision=decision))

    return results


def simplify_debts(
    debts: list[tuple[str, str, float]]
) -> list[DebtTransaction]:
    """
    Minimiert die Anzahl der Transaktionen für Schuldenausgleich.

    Die Reduktion läuft wie folgt:
    1. Berechne Nettosaldo jeder Person (Einnahmen - Schulden)
    2. Habe einer negativen Saldo → muss zahlen
    3. Habe einer positiven Saldo → bekommt Geld
    4. Greedy-Matching: Größter Schuldner zahlt an größten Gläubiger

    Parameters
    ----------
    debts : list of (schuldner, gläubiger, betrag)

    Returns
    -------
    list[DebtTransaction]  – minimierte Transaktionsliste
    """
    balances: dict[str, float] = {}
    for debtor, creditor, amount in debts:
        balances[debtor] = balances.get(debtor, 0.0) - amount
        balances[creditor] = balances.get(creditor, 0.0) + amount

    # Negative Salden: müssen zahlen; positive: bekommen
    payers = sorted([(p, -b) for p, b in balances.items() if b < -1e-9], key=lambda x: -x[1])
    receivers = sorted([(p, b) for p, b in balances.items() if b > 1e-9], key=lambda x: -x[1])

    transactions: list[DebtTransaction] = []
    pi, ri = 0, 0
    payers_list = list(payers)
    receivers_list = list(receivers)

    while pi < len(payers_list) and ri < len(receivers_list):
        payer, pay_amt = payers_list[pi]
        receiver, rec_amt = receivers_list[ri]
        transfer = min(pay_amt, rec_amt)
        transactions.append(DebtTransaction(payer=payer, receiver=receiver, amount=transfer))
        pay_amt -= transfer
        rec_amt -= transfer
        payers_list[pi] = (payer, pay_amt)
        receivers_list[ri] = (receiver, rec_amt)
        if pay_amt < 1e-9:
            pi += 1
        if rec_amt < 1e-9:
            ri += 1

    return transactions
