
from datetime import date, timedelta
from decimal import Decimal

from app.models import IncomePayment
from app.income_prediction import predict_income_date


def test_prediction_without_historical_data(db):
    """Bez historijskih uplata agent koristi očekivani datum."""

    future_income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    db.add(future_income)
    db.commit()

    result = predict_income_date(db, future_income)

    assert result["predicted_date"] == date(2026, 12, 15)
    assert result["average_delay"] == 0
    assert result["median_delay"] == 0
    assert result["sample_count"] == 0
    assert result["confidence"] == "Niska"


def test_prediction_uses_historical_average_delay(db):
    """Agent predviđa datum na osnovu prosječnog kašnjenja."""

    historical_payments = [
        IncomePayment(
            source_name="Plata",
            expected_date=date(2026, 10, 1),
            expected_amount=Decimal("1800.00"),
            actual_date=date(2026, 10, 5),
            actual_amount=Decimal("1800.00"),
            status="Received"
        ),
        IncomePayment(
            source_name="Plata",
            expected_date=date(2026, 10, 15),
            expected_amount=Decimal("1800.00"),
            actual_date=date(2026, 10, 20),
            actual_amount=Decimal("1800.00"),
            status="Received"
        ),
        IncomePayment(
            source_name="Plata",
            expected_date=date(2026, 11, 1),
            expected_amount=Decimal("1800.00"),
            actual_date=date(2026, 11, 6),
            actual_amount=Decimal("1800.00"),
            status="Received"
        ),
        IncomePayment(
            source_name="Plata",
            expected_date=date(2026, 11, 15),
            expected_amount=Decimal("1800.00"),
            actual_date=date(2026, 11, 21),
            actual_amount=Decimal("1800.00"),
            status="Received"
        )
    ]

    future_income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    db.add_all(historical_payments)
    db.add(future_income)
    db.commit()

    result = predict_income_date(db, future_income)

    assert result["average_delay"] == 5
    assert result["median_delay"] == 5
    assert result["sample_count"] == 4
    assert result["predicted_date"] == date(2026, 12, 20)
    assert result["confidence"] == "Umjerena"


def test_prediction_uses_only_same_income_source(db):
    """Historija jednog izvora ne utiče na drugi izvor."""

    salary = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 10, 1),
        expected_amount=Decimal("1800.00"),
        actual_date=date(2026, 10, 11),
        actual_amount=Decimal("1800.00"),
        status="Received"
    )

    freelance = IncomePayment(
        source_name="Freelance",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("500.00"),
        status="Expected"
    )

    db.add_all([salary, freelance])
    db.commit()

    result = predict_income_date(db, freelance)

    assert result["sample_count"] == 0
    assert result["average_delay"] == 0
    assert result["predicted_date"] == date(2026, 12, 15)
    assert result["confidence"] == "Niska"


def test_prediction_confidence_increases_with_more_history(db):
    """Pouzdanost raste s većim brojem historijskih uplata."""

    historical_payments = []

    for i in range(6):
        expected = date(2026, 1, 1) + timedelta(days=i * 30)

        historical_payments.append(
            IncomePayment(
                source_name="Plata",
                expected_date=expected,
                expected_amount=Decimal("1800.00"),
                actual_date=expected + timedelta(days=5),
                actual_amount=Decimal("1800.00"),
                status="Received"
            )
        )

    future_income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    db.add_all(historical_payments)
    db.add(future_income)
    db.commit()

    result = predict_income_date(db, future_income)

    assert result["sample_count"] == 6
    assert result["average_delay"] == 5
    assert result["predicted_date"] == date(2026, 12, 20)
    assert result["confidence"] == "Dobra"


def test_prediction_adapts_after_new_delayed_payment(db):
    """
    Provjerava da li novo iskustvo mijenja buduće predviđanje.
    """

    delays = [4, 5, 5, 6]
    historical_payments = []

    for i, delay in enumerate(delays):
        expected = date(2026, 10, 1) + timedelta(days=i * 10)

        historical_payments.append(
            IncomePayment(
                source_name="Plata",
                expected_date=expected,
                expected_amount=Decimal("1800.00"),
                actual_date=expected + timedelta(days=delay),
                actual_amount=Decimal("1800.00"),
                status="Received"
            )
        )

    future_income = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    db.add_all(historical_payments)
    db.add(future_income)
    db.commit()

    # Predviđanje prije novog iskustva.
    before_learning = predict_income_date(db, future_income)

    # Nova stvarno primljena uplata s kašnjenjem od 10 dana.
    new_payment = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 1),
        expected_amount=Decimal("1800.00"),
        actual_date=date(2026, 12, 11),
        actual_amount=Decimal("1800.00"),
        status="Received"
    )

    db.add(new_payment)
    db.commit()

    # Predviđanje nakon novog iskustva.
    after_learning = predict_income_date(db, future_income)

    assert before_learning["sample_count"] == 4
    assert before_learning["average_delay"] == 5
    assert before_learning["predicted_date"] == date(2026, 12, 20)

    assert after_learning["sample_count"] == 5
    assert after_learning["average_delay"] == 6
    assert after_learning["predicted_date"] == date(2026, 12, 21)

    assert after_learning["predicted_date"] > before_learning["predicted_date"]
