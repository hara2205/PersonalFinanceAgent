
from datetime import date
from decimal import Decimal

from app.agent import FinancialAgentRunner
from app.models import AccountState, IncomePayment, Obligation


def test_agent_sense_collects_financial_data(db):
    """Sense treba prikupiti trenutno stanje, prihode i obaveze."""

    account = AccountState(
        current_balance=Decimal("1500.00")
    )

    expected_income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 25),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    scheduled_income = IncomePayment(
        source_name="Freelance",
        expected_date=date(2026, 11, 20),
        expected_amount=Decimal("500.00"),
        actual_date=date(2026, 11, 22),
        actual_amount=Decimal("500.00"),
        status="ScheduledReceived"
    )

    obligation = Obligation(
        title="Stanarina",
        amount=Decimal("500.00"),
        due_date=date(2026, 11, 17),
        status="Pending"
    )

    db.add_all([
        account,
        expected_income,
        scheduled_income,
        obligation
    ])
    db.commit()

    agent = FinancialAgentRunner()
    result = agent.sense(db)

    assert result["balance"] == Decimal("1500.00")
    assert result["pending_income_count"] == 1
    assert result["scheduled_income_count"] == 1
    assert result["pending_obligation_count"] == 1


def test_agent_learns_from_received_payments_only(db):
    """Learn treba koristiti stvarno primljene uplate."""

    account = AccountState(
        current_balance=Decimal("2000.00")
    )

    received_salary = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 10, 1),
        expected_amount=Decimal("1500.00"),
        actual_date=date(2026, 10, 5),
        actual_amount=Decimal("1500.00"),
        status="Received"
    )

    received_freelance = IncomePayment(
        source_name="Freelance",
        expected_date=date(2026, 10, 10),
        expected_amount=Decimal("700.00"),
        actual_date=date(2026, 10, 13),
        actual_amount=Decimal("700.00"),
        status="Received"
    )

    expected_salary = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 25),
        expected_amount=Decimal("1500.00"),
        status="Expected"
    )

    db.add_all([
        account,
        received_salary,
        received_freelance,
        expected_salary
    ])
    db.commit()

    agent = FinancialAgentRunner()
    result = agent.learn(db)

    assert result["Plata"] == [4]
    assert result["Freelance"] == [3]
    assert len(result["Plata"]) == 1
    assert len(result["Freelance"]) == 1


def test_agent_sense_requires_account_state(db):
    """Sense treba prijaviti grešku ako stanje računa ne postoji."""

    agent = FinancialAgentRunner()

    try:
        agent.sense(db)
        assert False, "Ocekivana je ValueError greska."
    except ValueError as error:
        assert "Stanje racuna" in str(error)

from unittest.mock import patch


def test_agent_executes_complete_cycle(db):
    """Provjerava da agent izvršava sve četiri faze."""

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    salary = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 25),
        expected_amount=Decimal("1500.00"),
        actual_date=date(2026, 11, 25),
        actual_amount=Decimal("1500.00"),
        status="Received"
    )

    obligation = Obligation(
        title="Stanarina",
        amount=Decimal("500.00"),
        due_date=date(2026, 11, 20),
        status="Pending"
    )

    db.add_all([account, salary, obligation])
    db.commit()

    agent = FinancialAgentRunner()

    # Privremeno povezujemo agenta s testnom bazom.
    with patch(
        "app.agent.SessionLocal",
        return_value=db
    ):
        result = agent.step()

    assert result["financial_state"]["balance"] == Decimal("1000.00")
    assert result["analysis"]["cashflow"]["has_shortage"] is False
    assert result["decision"]["alert_created"] is False
    assert result["learned_sources"]["Plata"] == [0]
    assert result["execution_time"] is not None
