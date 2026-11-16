
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import mean

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import IncomePayment
from app.income_prediction import predict_income_date


# Odvojena demonstracijska baza
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DEMO_DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'demo_learning.db'}"

demo_engine = create_engine(
    DEMO_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

DemoSession = sessionmaker(
    bind=demo_engine,
    autoflush=False,
    autocommit=False
)


def prepare_learning_data(db):
    """
    Priprema izolovane podatke za demonstraciju ucenja.
    Glavna baza se ne koristi.
    """

    db.query(IncomePayment).delete()
    db.commit()

    # Sedam prethodnih uplata sa poznatim kasnjenjima.
    delays = [3, 4, 5, 4, 6, 5, 5]

    for index, delay in enumerate(delays):
        expected = date(2026, 1, 15) + timedelta(days=30 * index)

        payment = IncomePayment(
            source_name="Plata",
            expected_date=expected,
            expected_amount=Decimal("1800.00"),
            actual_date=expected + timedelta(days=delay),
            actual_amount=Decimal("1800.00"),
            status="Received"
        )

        db.add(payment)

    # Buduca plata koju agent treba predvidjeti.
    december_payment = IncomePayment(
        source_name="Plata",
        expected_date=date(2026, 12, 15),
        expected_amount=Decimal("1800.00"),
        status="Expected"
    )

    db.add(december_payment)
    db.commit()

    return december_payment


def demonstrate_learning():
    Base.metadata.create_all(bind=demo_engine)

    db = DemoSession()

    try:
        print("====================================")
        print(" DEMONSTRACIJA UCENJA AGENTA")
        print("====================================")
        print("Koristi se odvojena demo baza.")
        print("Glavna baza nije mijenjana.")

        december_payment = prepare_learning_data(db)

        # 1. Predvidjanje prije ucenja
        before = predict_income_date(db, december_payment)

        print("\n====================================")
        print(" PREDVIDJANJE PRIJE UCENJA")
        print("====================================")

        print("Ocekivani datum:", before["expected_date"])
        print("Predvidjeni datum:", before["predicted_date"])
        print("Prosjecno kasnjenje:", before["average_delay"])
        print("Broj historijskih uplata:", before["sample_count"])

        # 2. Dodavanje novog iskustva
        simulated_actual_date = date(2026, 11, 25)
        simulated_expected_date = date(2026, 11, 15)

        new_payment = IncomePayment(
            source_name="Plata",
            expected_date=simulated_expected_date,
            expected_amount=Decimal("1800.00"),
            actual_date=simulated_actual_date,
            actual_amount=Decimal("1800.00"),
            status="Received"
        )

        db.add(new_payment)
        db.commit()

        actual_delay = (
            simulated_actual_date - simulated_expected_date
        ).days

        print("\n====================================")
        print(" NOVO ISKUSTVO AGENTA")
        print("====================================")

        print("Ocekivani datum uplate:", simulated_expected_date)
        print("Stvarni datum uplate:", simulated_actual_date)
        print("Novo zabiljezeno kasnjenje:", actual_delay, "dana")

        # 3. Novo predvidjanje nakon ucenja
        after = predict_income_date(db, december_payment)

        print("\n====================================")
        print(" PREDVIDJANJE NAKON UCENJA")
        print("====================================")

        print("Ocekivani datum:", after["expected_date"])
        print("Predvidjeni datum:", after["predicted_date"])
        print("Prosjecno kasnjenje:", after["average_delay"])
        print("Broj historijskih uplata:", after["sample_count"])

        print("\n====================================")
        print(" REZULTAT UCENJA")
        print("====================================")

        if after["predicted_date"] > before["predicted_date"]:
            print("Agent je prilagodio predvidjanje!")
            print("Nova uplata je povecala prosjecno kasnjenje.")
        elif after["predicted_date"] < before["predicted_date"]:
            print("Agent je prilagodio predvidjanje.")
        else:
            print("Datum predvidjanja se nije promijenio.")

        print("\nGlavna baza podataka nije mijenjana.")

    finally:
        db.close()


if __name__ == "__main__":
    demonstrate_learning()
