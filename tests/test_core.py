"""Tests für fylab.core.portfolio, cashflow und currency – 100% Coverage"""
from datetime import date
import numpy as np
import pytest

from fylab.core.portfolio import Asset, AssetClass, Position, Portfolio
from fylab.core.cashflow import CashflowItem, CashflowPlan, Frequency
from fylab.core.currency import CurrencyConverter


# ═══════════════════════════════════════════════════════════════════════════
# Portfolio / Asset / Position
# ═══════════════════════════════════════════════════════════════════════════

def test_position_profit_loss():
    asset = Asset("AAPL", "Apple", AssetClass.STOCK)
    pos = Position(asset=asset, quantity=10, avg_buy_price=150.0, current_price=180.0)
    assert pos.profit_loss == pytest.approx(300.0)
    assert pos.profit_loss_pct == pytest.approx(20.0)


def test_position_profit_loss_zero_book_value():
    asset = Asset("X", "X", AssetClass.CASH)
    pos = Position(asset=asset, quantity=0, avg_buy_price=0.0, current_price=100.0)
    assert pos.profit_loss_pct == pytest.approx(0.0)


def test_position_market_and_book_value():
    asset = Asset("BND", "Bond", AssetClass.BOND)
    pos = Position(asset=asset, quantity=5, avg_buy_price=100.0, current_price=110.0)
    assert pos.market_value == pytest.approx(550.0)
    assert pos.book_value == pytest.approx(500.0)


def test_portfolio_weight():
    a1 = Asset("A", "A", AssetClass.STOCK)
    a2 = Asset("B", "B", AssetClass.STOCK)
    pf = Portfolio("Test")
    pf.positions = [
        Position(a1, 1, 100.0, 200.0),
        Position(a2, 1, 100.0, 200.0),
    ]
    assert pf.weight("A") == pytest.approx(0.5)
    assert pf.total_value == pytest.approx(400.0)


def test_portfolio_weight_unknown_symbol():
    pf = Portfolio("Test")
    a = Asset("A", "A", AssetClass.STOCK)
    pf.positions = [Position(a, 1, 100.0, 100.0)]
    assert pf.weight("UNKNOWN") == pytest.approx(0.0)


def test_portfolio_weight_zero_total():
    pf = Portfolio("Empty")
    assert pf.weight("A") == pytest.approx(0.0)


def test_portfolio_total_profit_loss():
    a1 = Asset("A", "A", AssetClass.STOCK)
    a2 = Asset("B", "B", AssetClass.STOCK)
    pf = Portfolio("P")
    pf.positions = [
        Position(a1, 1, 100.0, 120.0),
        Position(a2, 1, 100.0, 80.0),
    ]
    assert pf.total_profit_loss == pytest.approx(0.0)


def test_portfolio_weights_vector():
    a1 = Asset("A", "A", AssetClass.STOCK)
    a2 = Asset("B", "B", AssetClass.STOCK)
    pf = Portfolio("P")
    pf.positions = [Position(a1, 1, 100.0, 300.0), Position(a2, 1, 100.0, 100.0)]
    w = pf.weights_vector()
    assert w.sum() == pytest.approx(1.0)
    assert w[0] == pytest.approx(0.75)


def test_portfolio_weights_vector_empty():
    pf = Portfolio("Empty")
    w = pf.weights_vector()
    assert len(w) == 0


def test_portfolio_asset_class_allocation():
    a1 = Asset("A", "A", AssetClass.STOCK)
    a2 = Asset("B", "B", AssetClass.BOND)
    pf = Portfolio("P")
    pf.positions = [Position(a1, 1, 100.0, 200.0), Position(a2, 1, 100.0, 200.0)]
    alloc = pf.asset_class_allocation()
    assert "Aktie" in alloc
    assert "Anleihe" in alloc
    assert alloc["Aktie"] == pytest.approx(0.5)


def test_asset_hash():
    a = Asset("AAPL", "Apple", AssetClass.STOCK)
    b = Asset("AAPL", "Apple inc", AssetClass.ETF)
    assert hash(a) == hash(b)  # nur Symbol zählt


# ═══════════════════════════════════════════════════════════════════════════
# Cashflow
# ═══════════════════════════════════════════════════════════════════════════

def test_monthly_cashflow_sum():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Gehalt", 2000.0, date(2026, 1, 1), Frequency.MONTHLY, date(2026, 12, 31)),
        CashflowItem("Miete", -800.0, date(2026, 1, 1), Frequency.MONTHLY, date(2026, 12, 31)),
    ]
    monthly = plan.monthly_cashflow(2026)
    for val in monthly.values():
        assert val == pytest.approx(1200.0)


def test_once_cashflow():
    plan = CashflowPlan("Test")
    plan.items = [CashflowItem("Bonus", 5000.0, date(2026, 6, 1), Frequency.ONCE)]
    monthly = plan.monthly_cashflow(2026)
    assert "2026-06" in monthly
    assert monthly["2026-06"] == pytest.approx(5000.0)
    assert len(monthly) == 1


def test_once_cashflow_out_of_range():
    """Einmalige Zahlung außerhalb des Jahres taucht nicht auf."""
    plan = CashflowPlan("Test")
    plan.items = [CashflowItem("Old", 100.0, date(2025, 1, 1), Frequency.ONCE)]
    monthly = plan.monthly_cashflow(2026)
    assert len(monthly) == 0


def test_weekly_cashflow():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Wochenausgabe", -50.0, date(2026, 1, 5), Frequency.WEEKLY, date(2026, 1, 31))
    ]
    monthly = plan.monthly_cashflow(2026)
    assert "2026-01" in monthly
    assert monthly["2026-01"] < 0


def test_daily_cashflow():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Tagesausgabe", -1.0, date(2026, 1, 1), Frequency.DAILY, date(2026, 1, 31))
    ]
    monthly = plan.monthly_cashflow(2026)
    assert "2026-01" in monthly
    assert monthly["2026-01"] == pytest.approx(-31.0)


def test_quarterly_cashflow():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Quartal", 1000.0, date(2026, 1, 1), Frequency.QUARTERLY, date(2026, 12, 31))
    ]
    monthly = plan.monthly_cashflow(2026)
    # Sollte in Jan, Apr, Jul, Okt erscheinen
    assert "2026-01" in monthly
    assert "2026-04" in monthly


def test_yearly_cashflow():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Jahresbeitrag", -200.0, date(2026, 3, 1), Frequency.YEARLY, date(2027, 3, 1))
    ]
    monthly = plan.monthly_cashflow(2026)
    assert "2026-03" in monthly


def test_cumulative_cashflow_shape():
    plan = CashflowPlan("Test")
    plan.items = [
        CashflowItem("Gehalt", 1000.0, date(2026, 1, 1), Frequency.MONTHLY, date(2026, 12, 31))
    ]
    cum = plan.cumulative_cashflow(2026)
    assert len(cum) == 12
    assert cum[-1] == pytest.approx(12000.0)


# ═══════════════════════════════════════════════════════════════════════════
# Currency
# ═══════════════════════════════════════════════════════════════════════════

def test_currency_roundtrip():
    conv = CurrencyConverter()
    usd = conv.convert(100.0, "EUR", "USD")
    back = conv.convert(usd, "USD", "EUR")
    assert back == pytest.approx(100.0, rel=1e-6)


def test_invalid_currency_from():
    conv = CurrencyConverter()
    with pytest.raises(KeyError):
        conv.convert(100.0, "XYZ", "EUR")


def test_invalid_currency_to():
    conv = CurrencyConverter()
    with pytest.raises(KeyError):
        conv.convert(100.0, "EUR", "XYZ")


def test_update_rate():
    conv = CurrencyConverter()
    conv.update_rate("SEK", 11.5)
    sek = conv.convert(100.0, "EUR", "SEK")
    assert sek == pytest.approx(1150.0)


def test_update_rate_invalid():
    conv = CurrencyConverter()
    with pytest.raises(ValueError):
        conv.update_rate("USD", -1.0)


def test_currency_case_insensitive():
    conv = CurrencyConverter()
    a = conv.convert(100.0, "eur", "usd")
    b = conv.convert(100.0, "EUR", "USD")
    assert a == pytest.approx(b)


def test_currency_rate():
    conv = CurrencyConverter()
    r = conv.rate("EUR", "USD")
    assert r == pytest.approx(conv.convert(1.0, "EUR", "USD"))


def test_currency_available_currencies():
    conv = CurrencyConverter()
    avail = conv.available_currencies
    assert "EUR" in avail
    assert "USD" in avail
    assert avail == sorted(avail)  # sortiert


def test_currency_rate_matrix():
    conv = CurrencyConverter()
    currencies, matrix = conv.rate_matrix()
    n = len(currencies)
    assert len(matrix) == n
    assert len(matrix[0]) == n
    # Diagonale ist immer 1.0 (gleiche Währung)
    for i in range(n):
        assert matrix[i][i] == pytest.approx(1.0)
