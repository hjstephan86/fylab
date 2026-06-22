"""
fylab.analysis.portfolio_opt
=============================
Portfolio-Optimierung: Markowitz-Effizienzgrenze + MST-Diversifikation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from fylab.algorithms.mst import compute_portfolio_mst, MSTResult


@dataclass
class EfficientFrontierResult:
    """Ergebnisse der Effizienzgrenze."""
    returns: np.ndarray       # erwartete Renditen auf der Grenze
    volatilities: np.ndarray  # zugehörige Volatilitäten (Standardabweichungen)
    sharpe_ratios: np.ndarray
    optimal_weights: np.ndarray  # Gewichte des Sharpe-optimalen Portfolios
    optimal_return: float
    optimal_volatility: float
    optimal_sharpe: float


def compute_efficient_frontier(
    symbols: list[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.03,
    n_points: int = 100,
) -> EfficientFrontierResult:
    """
    Berechnet die Markowitz-Effizienzgrenze.

    Parameters
    ----------
    symbols : Asset-Symbole
    expected_returns : Erwartete jährliche Renditen (n,)
    cov_matrix : Kovarianzmatrix (n, n)
    risk_free_rate : Risikofreier Zinssatz
    n_points : Anzahl der Punkte auf der Grenze

    Returns
    -------
    EfficientFrontierResult
    """
    n = len(symbols)
    target_returns = np.linspace(expected_returns.min(), expected_returns.max(), n_points)
    vols: list[float] = []
    sharpes: list[float] = []

    def portfolio_vol(weights: np.ndarray) -> float:
        return float(np.sqrt(weights @ cov_matrix @ weights))

    def neg_sharpe(weights: np.ndarray) -> float:
        ret = float(weights @ expected_returns)
        vol = portfolio_vol(weights)
        return -(ret - risk_free_rate) / (vol + 1e-12)

    constraints_base = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.ones(n) / n

    for target in target_returns:
        constraints = constraints_base + [
            {"type": "eq", "fun": lambda w, t=target: w @ expected_returns - t}
        ]
        res = minimize(portfolio_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints)
        if res.success:
            vol = res.fun
        else:
            vol = portfolio_vol(w0)
        vols.append(vol)
        sharpe = (target - risk_free_rate) / (vol + 1e-12)
        sharpes.append(sharpe)

    # Sharpe-optimales Portfolio
    res_sharpe = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds,
                          constraints=constraints_base)
    opt_w = res_sharpe.x if res_sharpe.success else w0
    opt_ret = float(opt_w @ expected_returns)
    opt_vol = portfolio_vol(opt_w)
    opt_sharpe = (opt_ret - risk_free_rate) / (opt_vol + 1e-12)

    return EfficientFrontierResult(
        returns=target_returns,
        volatilities=np.array(vols),
        sharpe_ratios=np.array(sharpes),
        optimal_weights=opt_w,
        optimal_return=opt_ret,
        optimal_volatility=opt_vol,
        optimal_sharpe=opt_sharpe,
    )


def compute_diversification_mst(
    symbols: list[str],
    corr_matrix: np.ndarray,
) -> MSTResult:
    """Delegiert an fylab.algorithms.mst für Portfolio-MST."""
    return compute_portfolio_mst(symbols, corr_matrix)
