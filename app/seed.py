
import calendar
from datetime import date, timedelta
from decimal import Decimal

from app.database import Base, engine, SessionLocal
from app.models import (
    IncomePayment,
    Obligation,
    AccountState,
    AgentAlert
)


def get_month_date(year, month, day):
    """Vraca datum u odabranom mjesecu."""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def previous_month(current_date, months_back):
    """Vraca godinu i mjesec za prethodni period."""
    month_index = (
        current_date.year * 12
        + current_date.month - 1
        - months_back
    )

    year = month_index // 12
    month = month_index % 12 + 1

    return year, month


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Brisemo prethodne demonstracijske podatke.
        # Ovaj postupak koristimo samo za reset demonstracije.
        db.query(AgentAlert).delete()
        db.query(IncomePayment).delete()
        db.query(Obligation).delete()
        db.query(AccountState).delete()

        today = date.today()

        # --------------------------------------
        # 1. HISTORIJSKI PRIHODI
        # --------------------------------------

        for i in range(6, 0, -1):
            year, month = previous_month(today, i)

            expected_salary_date = get_month_date(
                year, month, 15
            )

            # Plata kasni 4 ili 5 dana.
            delay = 4 if i % 2 == 0 else 5

            actual_salary_date = (
                expected_salary_date + timedelta(days=delay)
            )

            salary = IncomePayment(
                source_name="Plata",
                expected_date=expected_salary_date,
                expected_amount=Decimal("1800.00"),
                actual_date=actual_salary_date,
                actual_amount=Decimal("1800.00"),
                status="Received"
            )

            db.add(salary)

            # Freelance prihodi nisu redovni.
            if i in [1, 3, 5]:
                expected_freelance_date = get_month_date(
                    year, month, 25
                )

                actual_freelance_date = (
                    expected_freelance_date
                    + timedelta(days=3 + (i % 2))
                )

                freelance = IncomePayment(
                    source_name="Freelance",
                    expected_date=expected_freelance_date,
                    expected_amount=Decimal("400.00"),
                    actual_date=actual_freelance_date,
                    actual_amount=Decimal("400.00"),
                    status="Received"
                )

                db.add(freelance)

            # ----------------------------------
            # 2. HISTORIJSKE OBAVEZE
            # ----------------------------------

            historical_obligations = [
                ("Stanarina", Decimal("500.00"), 17),
                ("Racuni", Decimal("200.00"), 20),
                ("Kredit", Decimal("300.00"), 22)
            ]

            for title, amount, due_day in historical_obligations:
                due_date = get_month_date(
                    year, month, due_day
                )

                obligation = Obligation(
                    title=title,
                    amount=amount,
                    due_date=due_date,
                    paid_date=due_date,
                    status="Paid"
                )

                db.add(obligation)

        # --------------------------------------
        # 3. TEKUCI OCEKIVANI PRIHOD
        # --------------------------------------

        current_salary = IncomePayment(
    source_name="Plata",
    expected_date=today + timedelta(days=4),
    expected_amount=Decimal("1800.00"),
    actual_date=None,
    actual_amount=None,
    status="Expected"
)

        db.add(current_salary)

        # --------------------------------------
        # 4. TEKUCE FINANSIJSKE OBAVEZE
        # --------------------------------------

        current_obligations = [
            ("Stanarina", Decimal("500.00"), 1),
            ("Racuni", Decimal("200.00"), 4),
            ("Kredit", Decimal("300.00"), 6)
        ]

        for title, amount, days_until_due in current_obligations:
            obligation = Obligation(
                title=title,
                amount=amount,
                due_date=today + timedelta(days=days_until_due),
                paid_date=None,
                status="Pending"
            )

            db.add(obligation)

        # --------------------------------------
        # 5. TRENUTNO STANJE RACUNA
        # --------------------------------------

        account = AccountState(
            current_balance=Decimal("600.00")
        )

        db.add(account)

        db.commit()

        print("Demonstracijski podaci su uspjesno kreirani!")

        print("\nTrenutno stanje racuna: 600 KM")
        print("Historijski period: 6 mjeseci")
        print("Ocekivana plata: 1800 KM")
        print("Ocekivani datum plate:", current_salary.expected_date)

        print("\nBroj evidentiranih uplata:",
              db.query(IncomePayment).count())

        print("Broj evidentiranih obaveza:",
              db.query(Obligation).count())

        print("Broj upozorenja:",
              db.query(AgentAlert).count())

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
