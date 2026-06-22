"""Tests für fylab.analysis – 100% Coverage"""
import numpy as np
import pytest

from fylab.analysis.risk import (
    compute_var_historical,
    compute_cvar_historical,
    compute_max_drawdown,
    compute_risk_metrics,
    monte_carlo_portfolio,
    RiskMetrics,
)
from fylab.analysis.portfolio_opt import compute_efficient_frontier


# ═══════════════════════════════════════════════════════════════════════════
# VaR / CVaR
# ═══════════════════════════════════════════════════════════════════════════

def test_var_positive():
    rng = np.random.default_rng(0)
    returns = rng.normal(0, 0.01, 1000)
    var = compute_var_historical(returns, 0.95)
    assert var > 0


def test_var_99_gt_var_95():
    rng = np.random.default_rng(0)
    returns = rng.normal(0, 0.01, 1000)
    var95 = compute_var_historical(returns, 0.95)
    var99 = compute_var_historical(returns, 0.99)
    assert var99 >= var95 - 1e-10


def test_cvar_ge_var():
    rng = np.random.default_rng(0)
    returns = rng.normal(0, 0.01, 1000)
    var = compute_var_historical(returns, 0.95)
    cvar = compute_cvar_historical(returns, 0.95)
    assert cvar >= var - 1e-10


def test_cvar_empty_tail():
    """Wenn kein Datenpunkt den VaR-Schwellwert unterschreitet, gibt CVaR = VaR zurück."""
    # Alle Renditen positiv → Tail-Schnitt leer
    returns = np.ones(100) * 0.01
    var = compute_var_historical(returns, 0.95)
    cvar = compute_cvar_historical(returns, 0.95)
    assert cvar == pytest.approx(var, abs=1e-6)


# ═══════════════════════════════════════════════════════════════════════════
# Max Drawdown
# ═══════════════════════════════════════════════════════════════════════════

def test_max_drawdown_zero_for_monotone():
    prices = np.arange(1, 101, dtype=float)
    dd = compute_max_drawdown(prices)
    assert dd == pytest.approx(0.0)


def test_max_drawdown_full_crash():
    prices = np.array([100.0, 50.0, 25.0])
    dd = compute_max_drawdown(prices)
    assert dd == pytest.approx(0.75)


def test_max_drawdown_recovery():
    prices = np.array([100.0, 80.0, 120.0])
    dd = compute_max_drawdown(prices)
    assert dd == pytest.approx(0.2)


# ═══════════════════════════════════════════════════════════════════════════
# compute_risk_metrics
# ═══════════════════════════════════════════════════════════════════════════

def test_risk_metrics_shape():
    rng = np.random.default_rng(1)
    returns = rng.normal(0.0003, 0.01, 500)
    metrics = compute_risk_metrics(returns)
    assert metrics.volatility_annual > 0
    assert isinstance(metrics.sharpe_ratio, float)


def test_risk_metrics_positive_sharpe_for_high_returns():
    returns = np.ones(252) * 0.001  # hohe positive tägliche Rendite
    metrics = compute_risk_metrics(returns, risk_free_rate=0.0)
    assert metrics.sharpe_ratio > 0


def test_risk_metrics_str():
    rng = np.random.default_rng(2)
    returns = rng.normal(0, 0.01, 200)
    m = compute_risk_metrics(returns)
    s = str(m)
    assert "VaR" in s
    assert "Sharpe" in s


# ═══════════════════════════════════════════════════════════════════════════
# Monte-Carlo
# ═══════════════════════════════════════════════════════════════════════════

def test_monte_carlo_shape():
    weights = np.array([1.0])
    means = np.array([0.1])
    cov = np.array([[0.04]])
    sims = monte_carlo_portfolio(weights, means, cov, n_simulations=100, n_days=50)
    assert sims.shape == (100, 51)
    assert np.all(sims[:, 0] == pytest.approx(100_000.0))


def test_monte_carlo_initial_value():
    weights = np.array([0.5, 0.5])
    means = np.array([0.08, 0.10])
    cov = np.array([[0.04, 0.01], [0.01, 0.04]])
    sims = monte_carlo_portfolio(weights, means, cov, n_simulations=50, n_days=10,
                                 initial_value=1000.0)
    assert np.all(sims[:, 0] == pytest.approx(1000.0))
    assert sims.shape == (50, 11)


# ═══════════════════════════════════════════════════════════════════════════
# Effizienzgrenze
# ═══════════════════════════════════════════════════════════════════════════

def test_efficient_frontier_shape():
    n = 4
    symbols = ["A", "B", "C", "D"]
    exp_ret = np.array([0.08, 0.12, 0.15, 0.10])
    rng = np.random.default_rng(10)
    A = rng.standard_normal((n, n))
    cov = A @ A.T / n * 0.04
    result = compute_efficient_frontier(symbols, exp_ret, cov, n_points=20)
    assert len(result.returns) == 20
    assert len(result.volatilities) == 20
    assert result.optimal_sharpe > -100


def test_efficient_frontier_optimal_weights_sum_to_one():
    symbols = ["A", "B"]
    exp_ret = np.array([0.08, 0.12])
    cov = np.array([[0.04, 0.01], [0.01, 0.04]])
    result = compute_efficient_frontier(symbols, exp_ret, cov, n_points=10)
    assert result.optimal_weights.sum() == pytest.approx(1.0, abs=1e-4)
