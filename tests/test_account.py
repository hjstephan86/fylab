"""Tests für fylab.core.account – 100% Coverage"""
from datetime import date
import pytest

from fylab.core.account import Account, AccountType, Transaction, TransactionCategory


# ═══════════════════════════════════════════════════════════════════════════
# Transaction
# ═══════════════════════════════════════════════════════════════════════════

def test_transaction_sign_income():
    t = Transaction(date(2026, 1, 1), 100.0, "test", TransactionCategory.INCOME, "T001")
    assert t.is_income
    assert not t.is_expense


def test_transaction_sign_expense():
    t = Transaction(date(2026, 1, 1), -100.0, "Miete", TransactionCategory.EXPENSE, "T001")
    assert t.is_expense
    assert not t.is_income


def test_transaction_repr_positive():
    t = Transaction(date(2026, 1, 1), 50.0, "Bonus", TransactionCategory.INCOME, "T001")
    r = repr(t)
    assert "+50.00" in r
    assert "Bonus" in r


def test_transaction_repr_negative():
    t = Transaction(date(2026, 1, 1), -50.0, "Gebühr", TransactionCategory.FEE, "T001")
    r = repr(t)
    assert "-50.00" in r


def test_transaction_with_counterparty_and_tags():
    t = Transaction(
        date(2026, 2, 1), 200.0, "Dividende", TransactionCategory.DIVIDEND, "D001",
        counter_party="Apple Inc", tags=["aktien", "us"]
    )
    assert t.counter_party == "Apple Inc"
    assert "aktien" in t.tags


# ═══════════════════════════════════════════════════════════════════════════
# Account
# ═══════════════════════════════════════════════════════════════════════════

def test_account_balance():
    acc = Account("T001", "Test", AccountType.CHECKING, initial_balance=1000.0)
    acc.add_transaction(Transaction(date(2026, 1, 1), 500.0, "Einnahme",
                                    TransactionCategory.INCOME, "T001"))
    acc.add_transaction(Transaction(date(2026, 1, 5), -200.0, "Ausgabe",
                                    TransactionCategory.EXPENSE, "T001"))
    assert acc.balance == pytest.approx(1300.0)


def test_account_balance_empty():
    acc = Account("T002", "Leer", AccountType.SAVINGS, initial_balance=500.0)
    assert acc.balance == pytest.approx(500.0)


def test_monthly_summary():
    acc = Account("T002", "Test", AccountType.CHECKING, initial_balance=0.0)
    acc.add_transaction(Transaction(date(2026, 1, 1), 1000.0, "Gehalt",
                                    TransactionCategory.INCOME, "T002"))
    acc.add_transaction(Transaction(date(2026, 1, 15), -400.0, "Miete",
                                    TransactionCategory.EXPENSE, "T002"))
    summary = acc.monthly_summary()
    assert "2026-01" in summary
    assert summary["2026-01"]["income"] == pytest.approx(1000.0)
    assert summary["2026-01"]["expense"] == pytest.approx(400.0)


def test_monthly_summary_multi_month():
    """Zwei Monate erscheinen getrennt im Summary."""
    acc = Account("T003", "Multimonate", AccountType.CHECKING, initial_balance=0.0)
    acc.add_transaction(Transaction(date(2026, 1, 10), 1000.0, "Jan",
                                    TransactionCategory.INCOME, "T003"))
    acc.add_transaction(Transaction(date(2026, 2, 10), 2000.0, "Feb",
                                    TransactionCategory.INCOME, "T003"))
    summary = acc.monthly_summary()
    assert "2026-01" in summary
    assert "2026-02" in summary
    assert summary["2026-01"]["income"] == pytest.approx(1000.0)
    assert summary["2026-02"]["income"] == pytest.approx(2000.0)


def test_monthly_summary_empty():
    acc = Account("T004", "Leer", AccountType.CASH, initial_balance=0.0)
    assert acc.monthly_summary() == {}


def test_transactions_by_category():
    acc = Account("T005", "Filter", AccountType.CHECKING, initial_balance=0.0)
    acc.add_transaction(Transaction(date(2026, 1, 1), 500.0, "Gehalt",
                                    TransactionCategory.INCOME, "T005"))
    acc.add_transaction(Transaction(date(2026, 1, 2), -50.0, "Internet",
                                    TransactionCategory.FEE, "T005"))
    acc.add_transaction(Transaction(date(2026, 1, 3), 100.0, "Dividende",
                                    TransactionCategory.DIVIDEND, "T005"))
    income_txns = acc.transactions_by_category(TransactionCategory.INCOME)
    assert len(income_txns) == 1
    fee_txns = acc.transactions_by_category(TransactionCategory.FEE)
    assert len(fee_txns) == 1


def test_account_all_types():
    """Sicherstellen, dass alle AccountType-Werte instanziierbar sind."""
    for at in AccountType:
        acc = Account("X", "X", at)
        assert acc.account_type == at


def test_transaction_all_categories():
    """Sicherstellen, dass alle TransactionCategory-Werte verwendbar sind."""
    for cat in TransactionCategory:
        t = Transaction(date(2026, 1, 1), 1.0, "test", cat, "ACC")
        assert t.category == cat
