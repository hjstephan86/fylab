"""
fylab.algorithms.mst
=====================
Minimum Spanning Tree für Portfolio-Diversifikation.

Problemstellung
---------------
Gegeben eine Korrelationsmatrix C ∈ ℝ^(n×n) von n Assets, berechne
den MST des vollständigen Graphen mit Kantengewichten d(i,j) = √(2(1−C_ij))
(Pearson-Distanz). Der MST zeigt die stärksten Abhängigkeiten im Portfolio.

Interpretation: Cluster im MST = stark korrelierte Assetgruppen.
Ein gut diversifiziertes Portfolio wählt Assets aus unterschiedlichen
MST-Clustern.

Algorithmus: Kruskal (Union-Find mit Pfadkompression + Union-by-Rank)
Komplexität: O(E log E) = O(n² log n) für vollständige Graphen

Reduktion
---------
Portfolio-Diversifikation ≤_p MST:
Konvertiere Korrelationsmatrix in Distanzgraph → MST-Berechnung → Cluster-Analyse
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from fylab.algorithms.subgraph_finance import subgraph_contains


@dataclass
class MSTResult:
    """Ergebnis der MST-Berechnung."""
    nodes: list[str]                      # Asset-Symbole (Knotenreihenfolge)
    edges: list[tuple[str, str, float]]   # MST-Kanten (u, v, Gewicht)
    total_weight: float
    clusters: list[list[str]]             # Gruppen ähnlicher Assets


def correlation_to_distance(corr_matrix: np.ndarray) -> np.ndarray:
    """
    Pearson-Distanzmetrik: d(i,j) = sqrt(2*(1 - rho_ij))
    d = 0 bedeutet vollständige positive Korrelation,
    d = 2 bedeutet vollständige negative Korrelation.
    """
    return np.sqrt(np.clip(2.0 * (1.0 - corr_matrix), 0.0, None))


# ---------------------------------------------------------------------------
# Union-Find (Kruskal-Hilfsdatenstruktur)
# ---------------------------------------------------------------------------

class _UnionFind:
    """Union-Find mit Pfadkompression und Union-by-Rank."""

    def __init__(self, nodes: list[str]) -> None:
        self._parent: dict[str, str] = {n: n for n in nodes}
        self._rank: dict[str, int] = {n: 0 for n in nodes}

    def find(self, x: str) -> str:
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])  # Pfadkompression
        return self._parent[x]

    def union(self, x: str, y: str) -> bool:
        """Vereinigt Mengen von x und y. Gibt False zurück bei gleichem Baum (Zyklus)."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        return True


# ---------------------------------------------------------------------------
# Verbundene Komponenten via DFS
# ---------------------------------------------------------------------------

def _connected_components(
    nodes: list[str],
    edges: list[tuple[str, str, float]],
) -> list[list[str]]:
    """Ermittelt verbundene Komponenten im ungerichteten Teilgraphen (DFS)."""
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for u, v, _ in edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    visited: set[str] = set()
    components: list[list[str]] = []
    for start in nodes:
        if start in visited:
            continue
        component: list[str] = []
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            stack.extend(adj.get(node, []))
        components.append(component)

    return components


# ---------------------------------------------------------------------------
# Kruskal-Algorithmus
# ---------------------------------------------------------------------------

def compute_portfolio_mst(
    symbols: list[str],
    corr_matrix: np.ndarray,
) -> MSTResult:
    """
    Berechnet den MST des Asset-Korrelationsgraphen via Kruskal-Algorithmus.

    Parameters
    ----------
    symbols : Asset-Symbole (Knotenbezeichnungen)
    corr_matrix : n×n Korrelationsmatrix

    Returns
    -------
    MSTResult
    """
    n = len(symbols)
    dist = correlation_to_distance(corr_matrix)

    # Alle Kanten aufstellen und nach Gewicht sortieren (Kruskal-Schritt 1)
    all_edges: list[tuple[float, str, str]] = [
        (float(dist[i, j]), symbols[i], symbols[j])
        for i in range(n)
        for j in range(i + 1, n)
    ]
    all_edges.sort()

    # Kanten hinzufügen solange kein Zyklus entsteht
    uf = _UnionFind(symbols)
    mst_edges: list[tuple[str, str, float]] = []
    for w, u, v in all_edges:
        if uf.union(u, v):
            mst_edges.append((u, v, w))
        if len(mst_edges) == n - 1:
            break

    total_weight = sum(w for _, _, w in mst_edges)

    # Cluster: verbundene Komponenten nach Entfernen schwacher Kanten (> Median)
    weights = [w for _, _, w in mst_edges]
    threshold = float(np.median(weights)) if weights else 0.0
    strong_edges = [(u, v, w) for u, v, w in mst_edges if w <= threshold]
    clusters = _connected_components(symbols, strong_edges)

    return MSTResult(
        nodes=symbols,
        edges=mst_edges,
        total_weight=total_weight,
        clusters=clusters,
    )


# ---------------------------------------------------------------------------
# Subgraph-basierter Portfolio-Strukturvergleich
# ---------------------------------------------------------------------------

@dataclass
class PortfolioStructureComparison:
    """
    Ergebnis des Subgraph-basierten Portfolio-Strukturvergleichs.

    Zwei Portfolios werden als binäre Korrelationsgraphen kodiert
    und per Subgraph Algorithmus verglichen.
    """
    decision: str        # Rohentscheidung des Subgraph Algorithmus
    a_in_b: bool         # Struktur A ⊆ Struktur B
    b_in_a: bool         # Struktur B ⊆ Struktur A
    description: str

    def __str__(self) -> str:
        return f"Portfolio-Vergleich: {self.description}  (decision={self.decision!r})"


def compare_portfolio_structures(
    symbols_a: list[str],
    corr_a: np.ndarray,
    symbols_b: list[str],
    corr_b: np.ndarray,
    threshold: float = 0.5,
) -> PortfolioStructureComparison:
    """
    Vergleicht die Korrelationsstrukturen zweier Portfolios via Subgraph-Isomorphismus.

    Binär-Kodierung: adj[i,j] = 1 wenn |corr[i,j]| > threshold (stark korreliert).
    Der Subgraph Algorithmus prüft ob die Struktur von A in B enthalten ist
    (Portfolio A ist strukturell in B „enthalten“, wenn B mindestens dieselben
    Korrelationsabhängigkeiten zeigt).

    STRUKTURVERGLEICH ≤_p SUBGRAPH_ISO  (optimale Laufzeit O(n³))

    Parameters
    ----------
    symbols_a, corr_a : Symbol-Liste und Korrelationsmatrix von Portfolio A
    symbols_b, corr_b : Symbol-Liste und Korrelationsmatrix von Portfolio B
    threshold : Korrelationsschwelle für starke Abhängigkeit (default 0.5)

    Returns
    -------
    PortfolioStructureComparison
    """
    def _corr_to_adj(corr: np.ndarray, thresh: float) -> np.ndarray:
        adj = (np.abs(corr) > thresh).astype(int)
        np.fill_diagonal(adj, 0)
        return adj

    A = _corr_to_adj(corr_a, threshold)
    B = _corr_to_adj(corr_b, threshold)

    # Subgraph Algorithmus: A ⊆ B?
    a_in_b, decision = subgraph_contains(A, B)
    # Umgekehrt: B ⊆ A?
    b_in_a, _ = subgraph_contains(B, A)

    if a_in_b and b_in_a:
        desc = "A und B sind strukturell äquivalent"
    elif a_in_b:
        desc = "A ist strukturell in B enthalten (B hat superset der Abhängigkeiten)"
    elif b_in_a:
        desc = "B ist strukturell in A enthalten (A hat superset der Abhängigkeiten)"
    else:
        desc = "Strukturen sind unvergleichbar (weder A⊆B noch B⊆A)"

    return PortfolioStructureComparison(
        decision=decision,
        a_in_b=a_in_b,
        b_in_a=b_in_a,
        description=desc,
    )
