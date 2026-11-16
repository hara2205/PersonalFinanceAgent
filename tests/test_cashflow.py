
from datetime import date
from decimal import Decimal

from app.models import AccountState, IncomePayment, Obligation
from app.cashflow_service import analyze_cashflow


def test_agent_detects_financial_shortage(db):
    """
    Testira da li agent prepoznaje nedostatak novca.

    Pocetni saldo: 600 KM
    Stanarina: 500 KM
    Racuni: 200 KM
    Kredit: 300 KM

    Ocekivani rezultat:
    Prvi manjak: 100 KM
    Najveci manjak: 400 KM
    """

    account = AccountState(
        current_balance=Decimal("600.00")
    )

    rent = Obligation(
        title="Stanarina",
        amount=Decimal("500.00"),
        due_date=date(2026, 11, 17),
        status="Pending"
    )

    bills = Obligation(
        title="Racuni",
        amount=Decimal("200.00"),
        due_date=date(2026, 11, 20),
        status="Pending"
    )

    loan = Obligation(
        title="Kredit",
        amount=Decimal("300.00"),
        due_date=date(2026, 11, 22),
        status="Pending"
    )

    db.add_all([
        account,
        rent,
        bills,
        loan
    ])

    db.commit()

    result = analyze_cashflow(db)

    assert result["starting_balance"] == Decimal("600.00")

    assert result["has_shortage"] is True

    assert result["first_shortage_date"] == date(2026, 11, 20)

    assert result["maximum_shortage"] == Decimal("400.00")

    assert result["final_balance"] == Decimal("-400.00")

    assert len(result["timeline"]) == 3

def test_obligation_is_processed_before_income_on_same_date(db):
    """
    Ako obaveza i prihod imaju isti datum,
    agent prvo obračunava obavezu.
    """

    same_date = date(2026, 11, 20)

    account = AccountState(
        current_balance=Decimal("500.00")
    )

    obligation = Obligation(
        title="Racuni",
        amount=Decimal("600.00"),
        due_date=same_date,
        status="Pending"
    )

    income = IncomePayment(
        source_name="Plata",
        expected_date=same_date,
        expected_amount=Decimal("1000.00"),
        actual_date=same_date,
        actual_amount=Decimal("1000.00"),
        status="ScheduledReceived"
    )

    db.add_all([account, obligation, income])
    db.commit()

    result = analyze_cashflow(db)

    assert result["has_shortage"] is True
    assert result["first_shortage_date"] == same_date
    assert result["maximum_shortage"] == Decimal("100.00")
    assert result["final_balance"] == Decimal("900.00")

    assert result["timeline"][0]["type"] == "OBAVEZA"
    assert result["timeline"][1]["type"] == "PRIHOD"


def test_agent_detects_temporary_shortage_before_later_income(db):
    """
    Agent mora prepoznati privremeni manjak
    čak i kada kasniji prihod popravi saldo.
    """

    account = AccountState(
        current_balance=Decimal("600.00")
    )

    income = IncomePayment(
        source_name="Freelance",
        expected_date=date(2026, 11, 25),
        expected_amount=Decimal("1000.00"),
        actual_date=date(2026, 11, 25),
        actual_amount=Decimal("1000.00"),
        status="ScheduledReceived"
    )

    obligations = [
        Obligation(
            title="Stanarina",
            amount=Decimal("500.00"),
            due_date=date(2026, 11, 17),
            status="Pending"
        ),
        Obligation(
            title="Racuni",
            amount=Decimal("200.00"),
            due_date=date(2026, 11, 20),
            status="Pending"
        )
    ]

    db.add(account)
    db.add(income)
    db.add_all(obligations)
    db.commit()

    result = analyze_cashflow(db)

    assert result["starting_balance"] == Decimal("600.00")
    assert result["has_shortage"] is True
    assert result["first_shortage_date"] == date(2026, 11, 20)
    assert result["maximum_shortage"] == Decimal("100.00")
    assert result["final_balance"] == Decimal("900.00")
