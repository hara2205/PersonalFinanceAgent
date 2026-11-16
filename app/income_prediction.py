
import math
from datetime import timedelta
from statistics import mean, median

from app.database import SessionLocal
from app.models import IncomePayment


def predict_income_date(db, income_payment):
    """
    Predvidja datum uplate na osnovu historijskih
    kasnjenja za isti izvor prihoda.
    """

    # Dohvatamo prethodne uspjesno primljene uplate
    historical_payments = (
        db.query(IncomePayment)
        .filter(
            IncomePayment.source_name == income_payment.source_name,
            IncomePayment.status == "Received",
            IncomePayment.actual_date.isnot(None)
        )
        .order_by(IncomePayment.actual_date)
        .all()
    )

    # Racunamo kasnjenje svake prethodne uplate
    delays = [
        (payment.actual_date - payment.expected_date).days
        for payment in historical_payments
    ]

    # Ako nemamo historijske podatke,
    # koristimo ocekivani datum
    if not delays:
        return {
            "source": income_payment.source_name,
            "expected_date": income_payment.expected_date,
            "predicted_date": income_payment.expected_date,
            "average_delay": 0,
            "median_delay": 0,
            "sample_count": 0,
            "confidence": "Niska",
            "method": "Bez historijskih podataka"
        }

    # Statisticka analiza prethodnih kasnjenja
    average_delay = mean(delays)
    median_delay = median(delays)

    # Za procjenu koristimo zaokruzivanje na veci
    # cijeli broj dana, kako ne bismo bili preoptimisticni
    predicted_delay = math.ceil(median_delay)

    predicted_date = (
        income_payment.expected_date
        + timedelta(days=predicted_delay)
    )

    # Kvalitativna procjena pouzdanosti
    if len(delays) < 3:
        confidence = "Niska"
    elif len(delays) < 6:
        confidence = "Umjerena"
    else:
        confidence = "Dobra"

    return {
        "source": income_payment.source_name,
        "expected_date": income_payment.expected_date,
        "predicted_date": predicted_date,
        "average_delay": round(average_delay, 2),
        "median_delay": median_delay,
        "sample_count": len(delays),
        "confidence": confidence,
        "method": "Historijska statisticka analiza"
    }


def main():
    db = SessionLocal()

    try:
        pending_payments = (
            db.query(IncomePayment)
            .filter(IncomePayment.status == "Expected")
            .order_by(IncomePayment.expected_date)
            .all()
        )

        if not pending_payments:
            print("Nema ocekivanih uplata.")
            return

        print("====================================")
        print(" PREDVIDJANJE DATUMA PRIHODA")
        print("====================================")

        for payment in pending_payments:
            result = predict_income_date(db, payment)

            print(f"\nIzvor prihoda: {result['source']}")
            print(f"Ocekivani datum: {result['expected_date']}")
            print(f"Predvidjeni datum: {result['predicted_date']}")
            print(f"Prosjecno kasnjenje: {result['average_delay']} dana")
            print(f"Broj historijskih uplata: {result['sample_count']}")
            print(f"Pouzdanost: {result['confidence']}")
            print(f"Metoda: {result['method']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
