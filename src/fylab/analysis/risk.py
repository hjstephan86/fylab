"""
fylab.analysis.risk
====================
Risikoanalyse: Value-at-Risk, CVaR, Monte-Carlo-Simulation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RiskMetrics:
    """Risikomaße eines Portfolios."""
    var_95: float   # Value-at-Risk (95 %)
    var_99: float   # Value-at-Risk (99 %)
    cvar_95: float  # Conditional VaR / Expected Shortfall (95 %)
    cvar_99: float  # Conditional VaR / Expected Shortfall (99 %)
    max_drawdown: float
    volatility_annual: float
    sharpe_ratio: float

    def __str__(self) -> str:
        return (
            f"VaR(95%)={self.var_95:.2%}  VaR(99%)={self.var_99:.2%}  "
            f"CVaR(95%)={self.cvar_95:.2%}  MaxDD={self.max_drawdown:.2%}  "
            f"Vol={self.volatility_annual:.2%}  Sharpe={self.sharpe_ratio:.2f}"
        )


def compute_var_historical(
    returns: np.ndarray,
    confidence: float = 0.95,
) -> float:
    """
    Historischer VaR: Quantil der Verteilung der Verluste.
    Positiver Rückgabewert = Verlust (z.B. 0.05 = 5 %).
    """
    return float(-np.percentile(returns, (1 - confidence) * 100))


def compute_cvar_historical(
    returns: np.ndarray,
    confidence: float = 0.95,
) -> float:
    """CVaR (Expected Shortfall): Erwarteter Verlust im schlimmsten Fall."""
    var = compute_var_historical(returns, confidence)
    tail = returns[returns <= -var]
    if len(tail) == 0:
        return var
    return float(-tail.mean())


def compute_max_drawdown(price_series: np.ndarray) -> float:
    """Maximaler relativer Rückgang vom Höchststand."""
    peak = np.maximum.accumulate(price_series)
    drawdown = (price_series - peak) / (peak + 1e-12)
    return float(-drawdown.min())


def compute_risk_metrics(
    returns: np.ndarray,
    risk_free_rate: float = 0.03,
) -> RiskMetrics:
    """
    Berechnet alle Risikomaße aus einer Zeitreihe von täglichen Renditen.

    Parameters
    ----------
    returns : tägliche Renditen (z.B. np.diff(log(prices)))
    risk_free_rate : jährlicher risikofreier Zins
    """
    var_95 = compute_var_historical(returns, 0.95)
    var_99 = compute_var_historical(returns, 0.99)
    cvar_95 = compute_cvar_historical(returns, 0.95)
    cvar_99 = compute_cvar_historical(returns, 0.99)

    vol_daily = float(returns.std())
    vol_annual = vol_daily * np.sqrt(252)

    mean_daily = float(returns.mean())
    mean_annual = mean_daily * 252
    sharpe = (mean_annual - risk_free_rate) / (vol_annual + 1e-12)

    # Max Drawdown aus kumulierten Preisen
    cum_prices = np.cumprod(1 + returns)
    max_dd = compute_max_drawdown(cum_prices)

    return RiskMetrics(
        var_95=var_95,
        var_99=var_99,
        cvar_95=cvar_95,
        cvar_99=cvar_99,
        max_drawdown=max_dd,
        volatility_annual=vol_annual,
        sharpe_ratio=sharpe,
    )


def monte_carlo_portfolio(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    n_simulations: int = 10_000,
    n_days: int = 252,
    initial_value: float = 100_000.0,
    seed: int = 42,
) -> np.ndarray:
    """
    Monte-Carlo-Simulation der Portfolioentwicklung.

    Returns
    -------
    np.ndarray (n_simulations, n_days+1) – simulierte Portfoliowerte
    """
    rng = np.random.default_rng(seed)
    portfolio_mean = float(weights @ mean_returns)
    portfolio_var = float(weights @ cov_matrix @ weights)

    # Tägliche Renditen aus Normalverteilung
    daily_mean = portfolio_mean / 252
    daily_std = np.sqrt(portfolio_var / 252)

    simulations = np.zeros((n_simulations, n_days + 1))
    simulations[:, 0] = initial_value
    for t in range(1, n_days + 1):
        daily_returns = rng.normal(daily_mean, daily_std, n_simulations)
        simulations[:, t] = simulations[:, t - 1] * (1 + daily_returns)
    return simulations
