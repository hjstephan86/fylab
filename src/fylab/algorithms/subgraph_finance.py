"""
fylab.algorithms.subgraph_finance
==================================
Subgraph-Isomorphismus für Finanzmuster-Erkennung.

Verwendet denselben Subgraph Algorithmus wie pylabb
(git+https://gitlab.com/epp-group/subgraph.git@v1.0.0).

Problemstellung
---------------
Gegeben einen Transaktionsgraphen G = (V, E) und einen Muster-Graphen
R = (V_R, E_R) (z.B. ein bekanntes Betrugsmuster), prüfe ob R ⊆ G gilt
(R ist als Subgraph in G enthalten).

Algorithmus
-----------
Die ``Subgraph``-Klasse vergleicht binäre Adjazenzmatrizen mittels
zyklischer Spalten-Rotation und polynomialer Hash-Signaturen (O(n³)).

Rückgabe-Entscheidungen von ``Subgraph.compare_graphs(R, G)``:
  "keep_B"       → G enthält R  (R ⊆ G) → Muster erkannt
  "keep_A"       → R enthält G  (G ⊆ R) → kein Muster
  "equal_keep_A" → R ⊆ G und G ⊆ R     → Muster erkannt
  "equal_keep_B" → R ⊆ G und G ⊆ R     → Muster erkannt
  "keep_both"    → weder R ⊆ G noch G ⊆ R → kein Muster

Polynomielle Reduktion
----------------------
    FRAUD_DETECT ≤_p SUBGRAPH_ISO

Jede Transaktion = Knoten, jeder Zahlungsfluss = gerichtete Kante.
Bekannte Betrugsstruktur wird als Referenz-Adjazenzmatrix R kodiert.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

# Gerichteter Adjazenzgraph: {sender: {empfänger: betrag}}
AdjGraph = dict[str, dict[str, float]]


class FraudPattern(Enum):
    """Bekannte Betrugsschemen als Subgraph-Muster."""
    WASH_TRADING  = "Wash-Trading (Kreiszahlung)"
    SMURFING      = "Smurfing (Sternverteilung)"
    LAYERING      = "Layering (Kettenstruktur)"
    CIRCULAR_FLOW = "Kreisfluss (Ringstruktur)"


# ---------------------------------------------------------------------------
# Referenz-Adjazenzmatrizen der Betrugsmuster (analog _REFERENCE_TOPOLOGIES in
# pylabb.control.bio_classify)
# ---------------------------------------------------------------------------

#: Wash-Trading: A → B → A  (2-Kreis)
_WASH_TRADING_REF = np.array(
    [[0, 1],
     [1, 0]],
    dtype=int,
)

#: Smurfing: Zentralknoten → 4 Empfänger (Stern)
_SMURFING_REF = np.array(
    [[0, 1, 1, 1, 1],
     [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]],
    dtype=int,
)

#: Layering: A → B → C → D  (Kette)
_LAYERING_REF = np.array(
    [[0, 1, 0, 0],
     [0, 0, 1, 0],
     [0, 0, 0, 1],
     [0, 0, 0, 0]],
    dtype=int,
)

#: Circular Flow: A → B → C → A  (3-Zyklus)
_CIRCULAR_FLOW_REF = np.array(
    [[0, 1, 0],
     [0, 0, 1],
     [1, 0, 0]],
    dtype=int,
)

PATTERN_MATRICES: dict[FraudPattern, np.ndarray] = {
    FraudPattern.WASH_TRADING:  _WASH_TRADING_REF,
    FraudPattern.SMURFING:      _SMURFING_REF,
    FraudPattern.LAYERING:      _LAYERING_REF,
    FraudPattern.CIRCULAR_FLOW: _CIRCULAR_FLOW_REF,
}


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Transaktionsgraph → Adjazenzmatrix
# (analog loop_to_graph / _to_adjacency_matrix in pylabb.control.verification)
# ---------------------------------------------------------------------------

def _transaction_graph_to_matrix(
    graph: AdjGraph,
) -> tuple[np.ndarray, list]:
    """
    Konvertiert einen Adjazenzdict-Graphen in eine binäre Adjazenzmatrix.

    Parameters
    ----------
    graph : AdjGraph – {sender: {empfänger: betrag}}

    Returns
    -------
    (adj_matrix, node_list)
        adj_matrix : binäre n×n Adjazenzmatrix (int)
        node_list  : geordnete Knotenliste (Index = Zeilennummer)
    """
    nodes = list(graph.keys())
    n = len(nodes)
    idx = {node: i for i, node in enumerate(nodes)}
    adj = np.zeros((n, n), dtype=int)
    for u, targets in graph.items():
        for v in targets:
            if v in idx:
                adj[idx[u]][idx[v]] = 1
    return adj, nodes


def _pad_matrix(M: np.ndarray, target_n: int) -> np.ndarray:
    """Erweitert eine quadratische Matrix auf target_n × target_n (Null-Padding).
    Analog _pad_matrix in pylabb.control.bio_classify."""
    n = M.shape[0]
    if n >= target_n:
        return M.copy()
    padded = np.zeros((target_n, target_n), dtype=M.dtype)
    padded[:n, :n] = M
    return padded


# ---------------------------------------------------------------------------
# Ergebnis-Datenklasse
# ---------------------------------------------------------------------------

@dataclass
class FraudDetectionResult:
    """Ergebnis der Subgraph-basierten Betrugserkennung."""
    pattern: FraudPattern
    detected: bool
    decision: str          # Rohentscheidung des Subgraph Algorithmus
    mapping: Optional[dict] = None  # Knotenindizes-Mapping (sofern verfügbar)

    def __str__(self) -> str:
        status = "ERKANNT" if self.detected else "nicht gefunden"
        return f"[{status}] {self.pattern.value}  (decision={self.decision!r})"


# ---------------------------------------------------------------------------
# Transaktionsgraph aufbauen
# ---------------------------------------------------------------------------

def build_transaction_graph(transactions: list[tuple[str, str, float]]) -> AdjGraph:
    """
    Erstellt einen Transaktionsgraphen aus einer Liste von Überweisungen.

    Parameters
    ----------
    transactions : list of (sender, receiver, amount)

    Returns
    -------
    AdjGraph – {sender: {empfänger: betrag}}, alle beteiligten Knoten als Keys
    """
    g: AdjGraph = {}
    for sender, receiver, amount in transactions:
        g.setdefault(sender, {})
        g.setdefault(receiver, {})  # Empfänger-Knoten sicherstellen
        if receiver in g[sender]:
            g[sender][receiver] += amount
        else:
            g[sender][receiver] = amount
    return g


# ---------------------------------------------------------------------------
# Kern-Utility: direkte Subgraph-Vergleich-Funktion
# Wird von subgraph_finance, arbitrage, max_flow und mst gemeinsam genutzt.
# (analog _compare_topology in pylabb.control.verification)
# ---------------------------------------------------------------------------

def subgraph_contains(
    R: np.ndarray,
    G: np.ndarray,
    use_adjacency_list: bool = False,
) -> tuple[bool, str]:
    """
    Prüft ob Muster-Matrix R als Subgraph in Matrix G enthalten ist.

    Die Matrizen werden automatisch auf gemeinsame Größe gepaddet.
    Identisch mit dem Aufrufmuster aus pylabb.control.verification.

    Parameters
    ----------
    R : Referenz-/Muster-Adjazenzmatrix (int oder float)
    G : Graph-Adjazenzmatrix (der zu durchsuchende Graph)
    use_adjacency_list : Adjazenzlisten-Variante (für dichte Graphen)

    Returns
    -------
    (detected, decision)
        detected : True wenn R ⊆ G
        decision : Rohentscheidung des Subgraph Algorithmus
    """
    try:
        from subgraph import Subgraph  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "Das Paket 'subgraph' fehlt.\n"
            "  pip install git+https://gitlab.com/epp-group/subgraph.git@v1.0.0"
        ) from exc

    n_max = max(R.shape[0], G.shape[0])
    R_padded = _pad_matrix(R, n_max).astype(float)
    G_padded = _pad_matrix(G, n_max).astype(float)
    algo = Subgraph(use_adjacency_list=use_adjacency_list)
    if use_adjacency_list:
        decision, _ = algo.compare_graphs_with_adj_list(R_padded, G_padded)
    else:
        decision, _ = algo.compare_graphs(R_padded, G_padded)
    detected = decision in ("keep_B", "equal_keep_A", "equal_keep_B", "equal")
    return detected, decision


# ---------------------------------------------------------------------------
# Subgraph-Isomorphismus-Überprüfung via Subgraph-Paket
# (analog verify_loops in pylabb.control.verification)
# ---------------------------------------------------------------------------

def detect_fraud_patterns(
    transaction_graph: AdjGraph,
    patterns: list[FraudPattern] | None = None,
    use_adjacency_list: bool = False,
) -> list[FraudDetectionResult]:
    """
    Prüft den Transaktionsgraphen auf bekannte Betrugsmuster mittels des
    Subgraph Algorithmus (identisch wie in pylabb verwendet).

    Für jedes Muster R wird die Adjazenzmatrix des Musters mit der
    Adjazenzmatrix des Transaktionsgraphen G verglichen:
    Entscheidung ``"keep_B"`` oder ``"equal_*"`` bedeutet R ⊆ G.

    Parameters
    ----------
    transaction_graph : Transaktionsnetzwerk als nx.DiGraph
    patterns : zu prüfende Muster (None = alle)
    use_adjacency_list : wenn True, Adjazenzlisten-Variante nutzen
                         (für dichte Graphen, analog pylabb)

    Returns
    -------
    list[FraudDetectionResult]

    Raises
    ------
    ImportError : wenn das ``subgraph``-Paket nicht installiert ist.
    """
    if patterns is None:
        patterns = list(FraudPattern)

    G_matrix, _ = _transaction_graph_to_matrix(transaction_graph)

    results: list[FraudDetectionResult] = []
    for pattern in patterns:
        R = PATTERN_MATRICES[pattern]
        # subgraph_contains kümmert sich um Padding und Subgraph-Aufruf
        detected, decision = subgraph_contains(R, G_matrix, use_adjacency_list)
        results.append(FraudDetectionResult(
            pattern=pattern,
            detected=detected,
            decision=decision,
        ))

    return results
