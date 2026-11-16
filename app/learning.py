
from datetime import date
from decimal import Decimal

from app.database import SessionLocal
from app.models import IncomePayment
from app.income_prediction import predict_income_date


def demonstrate_learning():
    db = SessionLocal()

    try:
        # Pronalazimo novembarsku platu
        november_payment = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.source_name == "Plata",
                IncomePayment.expected_date == date(2026, 11, 15)
            )
            .first()
        )

        if november_payment is None:
            print("Novembarska plata nije pronadjena.")
            return

        # Demonstraciju izvodimo samo jednom.
        if november_payment.status == "Received":
            print("Demonstracija ucenja je vec izvrsena.")
            return

        # Kreiramo ocekivanu decembarsku platu
        december_payment = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.source_name == "Plata",
                IncomePayment.expected_date == date(2026, 12, 15)
            )
            .first()
        )

        if december_payment is None:
            december_payment = IncomePayment(
                source_name="Plata",
                expected_date=date(2026, 12, 15),
                expected_amount=Decimal("1800.00"),
                status="Expected"
            )

            db.add(december_payment)
            db.flush()

        # --------------------------------------
        # 1. PREDVIDJANJE PRIJE UCENJA
        # --------------------------------------

        before = predict_income_date(
            db,
            december_payment
        )

        print("====================================")
        print(" PREDVIDJANJE PRIJE UCENJA")
        print("====================================")

        print("Ocekivani datum:", before["expected_date"])
        print("Predvidjeni datum:", before["predicted_date"])
        print("Prosjecno kasnjenje:", before["average_delay"])
        print("Broj historijskih uplata:", before["sample_count"])

        # --------------------------------------
        # 2. SIMULACIJA NOVE STVARNE UPLATE
        # --------------------------------------

        # U ovoj demonstraciji simuliramo da je
        # novembarska plata stigla 25. novembra.
        simulated_actual_date = date(2026, 11, 25)

        november_payment.actual_date = simulated_actual_date
        november_payment.actual_amount = (
            november_payment.expected_amount
        )
        november_payment.status = "Received"

        db.commit()

        actual_delay = (
            november_payment.actual_date
            - november_payment.expected_date
        ).days

        print("\n====================================")
        print(" NOVO ISKUSTVO AGENTA")
        print("====================================")

        print("Ocekivana uplata:", november_payment.expected_date)
        print("Simulirana stvarna uplata:", november_payment.actual_date)
        print("Novo zabiljezeno kasnjenje:", actual_delay, "dana")

        # --------------------------------------
        # 3. PREDVIDJANJE NAKON UCENJA
        # --------------------------------------

        after = predict_income_date(
            db,
            december_payment
        )

        print("\n====================================")
        print(" PREDVIDJANJE NAKON UCENJA")
        print("====================================")

        print("Ocekivani datum:", after["expected_date"])
        print("Predvidjeni datum:", after["predicted_date"])
        print("Prosjecno kasnjenje:", after["average_delay"])
        print("Broj historijskih uplata:", after["sample_count"])

        print("\n====================================")

        if before["predicted_date"] != after["predicted_date"]:
            print("Agent je prilagodio svoje predvidjanje!")
        else:
            print("Predvidjanje se nije promijenilo.")

    finally:
        db.close()


if __name__ == "__main__":
    demonstrate_learning()
