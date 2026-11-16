
from datetime import date
from decimal import Decimal

from app.models import AccountState, IncomePayment, Obligation
from app.cashflow_service import analyze_cashflow


def test_scheduled_income_prevents_final_shortage(db):
    """
    Testira obracun unaprijed evidentirane buduce uplate.

    Pocetni saldo: 600 KM
    Obaveze: 1.000 KM
    Buduca plata: 1.800 KM

    Plata pristize 25.11.2026.
    Ocekivani konacni saldo: 1.400 KM.
    """

    account = AccountState(
        current_balance=Decimal("600.00")
    )

    salary = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 20),
        expected_amount=Decimal("1800.00"),
        actual_date=date(2026, 11, 25),
        actual_amount=Decimal("1800.00"),
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
        ),
        Obligation(
            title="Kredit",
            amount=Decimal("300.00"),
            due_date=date(2026, 11, 22),
            status="Pending"
        )
    ]

    db.add(account)
    db.add(salary)
    db.add_all(obligations)
    db.commit()

    result = analyze_cashflow(db)

    assert result["starting_balance"] == Decimal("600.00")

    assert result["has_shortage"] is True

    assert result["first_shortage_date"] == date(2026, 11, 20)

    assert result["maximum_shortage"] == Decimal("400.00")

    assert result["final_balance"] == Decimal("1400.00")

    assert result["timeline"][-1]["type"] == "PRIHOD"

    assert result["timeline"][-1]["date"] == date(2026, 11, 25)
