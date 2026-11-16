
from datetime import date
from decimal import Decimal

from app.models import AccountState, Obligation, AgentAlert
from app.decisions import make_agent_decision


def test_agent_creates_alert_when_shortage_is_detected(db):
    """Agent treba kreirati upozorenje kada predvidi manjak novca."""

    account = AccountState(
        current_balance=Decimal("600.00")
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
    db.add_all(obligations)
    db.commit()

    result = make_agent_decision(db)

    alerts = db.query(AgentAlert).all()

    assert result["alert_created"] is True
    assert len(alerts) == 1
    assert alerts[0].is_active is True
    assert alerts[0].shortage_date == date(2026, 11, 20)
    assert alerts[0].shortage_amount == Decimal("100.00")


def test_agent_updates_existing_alert_instead_of_creating_duplicate(db):
    """Agent treba ažurirati postojeće upozorenje, bez duplikata."""

    account = AccountState(
        current_balance=Decimal("600.00")
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
    db.add_all(obligations)
    db.commit()

    first_result = make_agent_decision(db)
    second_result = make_agent_decision(db)

    alerts = db.query(AgentAlert).all()

    assert first_result["alert_created"] is True
    assert second_result["alert_created"] is False
    assert second_result["alert_updated"] is True
    assert len(alerts) == 1
    assert alerts[0].is_active is True


def test_agent_deactivates_alert_when_shortage_disappears(db):
    """Agent treba deaktivirati upozorenje kada više nema manjka."""

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    obligation = Obligation(
        title="Stanarina",
        amount=Decimal("500.00"),
        due_date=date(2026, 11, 17),
        status="Pending"
    )

    old_alert = AgentAlert(
        shortage_date=date(2026, 11, 20),
        shortage_amount=Decimal("100.00"),
        message="Predvidjen je nedostatak novca.",
        confidence=Decimal("0.2500"),
        is_active=True
    )

    db.add(account)
    db.add(obligation)
    db.add(old_alert)
    db.commit()

    result = make_agent_decision(db)

    db.refresh(old_alert)

    assert result["alert_created"] is False
    assert old_alert.is_active is False

def test_agent_assesses_high_financial_risk():
    from datetime import date, timedelta
    from app.decisions import assess_risk

    result = assess_risk(
        date.today() + timedelta(days=2),
        Decimal("100.00"),
        Decimal("200.00")
    )

    assert result["risk_level"] == "HIGH"
    assert result["days_remaining"] == 2


def test_agent_assesses_medium_financial_risk():
    from datetime import date, timedelta
    from app.decisions import assess_risk

    result = assess_risk(
        date.today() + timedelta(days=5),
        Decimal("100.00"),
        Decimal("200.00")
    )

    assert result["risk_level"] == "MEDIUM"
    assert result["days_remaining"] == 5


def test_agent_assesses_low_financial_risk():
    from datetime import date, timedelta
    from app.decisions import assess_risk

    result = assess_risk(
        date.today() + timedelta(days=10),
        Decimal("100.00"),
        Decimal("200.00")
    )

    assert result["risk_level"] == "LOW"
    assert result["days_remaining"] == 10
