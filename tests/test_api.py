
from decimal import Decimal
from datetime import date
from app.models import AccountState, IncomePayment, Obligation


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "Personal Finance Agent"
    assert data["status"] == "running"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_financial_overview_endpoint(client, db):
    account = AccountState(
        current_balance=Decimal("1500.00")
    )

    income = IncomePayment(
        source_name="Plata",
        expected_date=__import__("datetime").date(2026, 12, 1),
        expected_amount=Decimal("2000.00"),
        status="Expected"
    )

    obligation = Obligation(
        title="Stanarina",
        amount=Decimal("500.00"),
        due_date=__import__("datetime").date(2026, 11, 20),
        status="Pending"
    )

    db.add_all([account, income, obligation])
    db.commit()

    response = client.get("/finance/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["current_balance"] == 1500.0
    assert len(data["expected_incomes"]) == 1
    assert len(data["pending_obligations"]) == 1

    assert data["expected_incomes"][0]["source"] == "Plata"
    assert data["pending_obligations"][0]["title"] == "Stanarina"

    assert data["active_alerts_count"] == 0

def test_financial_forecast_endpoint(client, db):
    from datetime import date

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

    db.add_all([account, rent, bills, loan])
    db.commit()

    response = client.get("/finance/forecast")

    assert response.status_code == 200

    data = response.json()

    assert data["starting_balance"] == 600.0
    assert data["has_shortage"] is True
    assert data["first_shortage_date"] == "2026-11-20"
    assert data["maximum_shortage"] == 400.0
    assert data["final_balance"] == -400.0

    assert len(data["timeline"]) == 3

def test_receive_income_updates_balance_immediately(client, db):
    """
    Testira evidentiranje vec primljenog prihoda.

    Ocekivano:
    - Status prihoda postaje Received.
    - Saldo se odmah povecava.
    """

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 15),
        expected_amount=Decimal("1500.00"),
        status="Expected"
    )

    db.add_all([account, income])
    db.commit()
    db.refresh(income)

    response = client.post(
        f"/incomes/{income.id}/receive",
        json={
            "actual_date": "2026-11-16",
            "actual_amount": 1500.00
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["income"]["status"] == "Received"
    assert data["income"]["delay_days"] == 1
    assert data["new_account_balance"] == 2500.0


def test_receive_future_income_does_not_update_balance(
    client,
    db
):
    """
    Testira evidentiranje buduceg prihoda.

    Ocekivano:
    - Status prihoda postaje ScheduledReceived.
    - Saldo se ne povecava odmah.
    """

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    income = IncomePayment(
        source_name="Freelance",
        expected_date=date(2026, 11, 20),
        expected_amount=Decimal("800.00"),
        status="Expected"
    )

    db.add_all([account, income])
    db.commit()
    db.refresh(income)

    response = client.post(
        f"/incomes/{income.id}/receive",
        json={
            "actual_date": "2026-11-25",
            "actual_amount": 800.00
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["income"]["status"] == "ScheduledReceived"
    assert data["income"]["delay_days"] == 5
    assert data["new_account_balance"] == 1000.0

def test_receive_income_twice_returns_conflict(client, db):
    """
    Testira da li sistem sprjecava dvostruko
    evidentiranje istog prihoda.
    """

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 11, 15),
        expected_amount=Decimal("1500.00"),
        status="Expected"
    )

    db.add_all([account, income])
    db.commit()
    db.refresh(income)

    first_response = client.post(
        f"/incomes/{income.id}/receive",
        json={
            "actual_date": "2026-11-16",
            "actual_amount": 1500.00
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/incomes/{income.id}/receive",
        json={
            "actual_date": "2026-11-16",
            "actual_amount": 1500.00
        }
    )

    assert second_response.status_code == 409

    assert db.query(AccountState).first().current_balance == Decimal("2500.00")

def test_alerts_endpoint_returns_active_alerts(client, db):
    from datetime import date

    from app.models import AgentAlert

    alert = AgentAlert(
        shortage_date=date(2026, 11, 20),
        shortage_amount=Decimal("250.00"),
        message="Predvidjen je nedostatak novca.",
        confidence=Decimal("0.7500"),
        is_active=True
    )

    inactive_alert = AgentAlert(
        shortage_date=date(2026, 11, 25),
        shortage_amount=Decimal("100.00"),
        message="Staro upozorenje.",
        confidence=Decimal("0.5000"),
        is_active=False
    )

    db.add_all([alert, inactive_alert])
    db.commit()

    response = client.get("/alerts")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["alerts"]) == 1

    returned_alert = data["alerts"][0]

    assert returned_alert["shortage_date"] == "2026-11-20"
    assert returned_alert["shortage_amount"] == 250.0
    assert returned_alert["confidence"] == 0.75
    assert returned_alert["is_active"] is True

