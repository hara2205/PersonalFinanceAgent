
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    AccountState,
    IncomePayment,
    Obligation
)
from app.agent import FinancialAgentRunner


# ==========================================
# 1. POSEBNA DEMONSTRACIJSKA BAZA
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DEMO_DATABASE_URL = (
    f"sqlite:///{DATABASE_DIR / 'demo_finance.db'}"
)

demo_engine = create_engine(
    DEMO_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

DemoSession = sessionmaker(
    bind=demo_engine,
    autoflush=False,
    autocommit=False
)


# ==========================================
# 2. PRIPREMA DEMONSTRACIJSKIH PODATAKA
# ==========================================

def prepare_demo_data(db):
    """
    Kreira ponovljiv demonstracijski scenario.

    Brise i ponovo kreira tabele iskljucivo
    u demonstracijskoj bazi.
    """

    Base.metadata.drop_all(bind=demo_engine)
    Base.metadata.create_all(bind=demo_engine)

    today = date.today()

    # Pocetno stanje racuna
    account = AccountState(
        current_balance=Decimal("2400.00")
    )

    db.add(account)

    # Historijska kasnjenja plate.
    # Prosjek kasnjenja je 4.57 dana.
    historical_delays = [3, 4, 5, 4, 6, 5, 5]

    for index, delay in enumerate(historical_delays):

        actual_date = today - timedelta(
            days=30 - index * 3
        )

        expected_date = actual_date - timedelta(
            days=delay
        )

        payment = IncomePayment(
            source_name="Plata",
            expected_date=expected_date,
            expected_amount=Decimal("2000.00"),
            actual_date=actual_date,
            actual_amount=Decimal("2000.00"),
            status="Received"
        )

        db.add(payment)

    # Ocekivana plata.
    # Agent ce na osnovu historije predvidjeti
    # kasnjenje od 5 dana.
    expected_salary = IncomePayment(
        source_name="Plata",
        expected_date=today + timedelta(days=2),
        expected_amount=Decimal("2000.00"),
        status="Expected"
    )

    db.add(expected_salary)

    # Finansijske obaveze.
    obligations = [
        Obligation(
            title="Stanarina",
            amount=Decimal("1000.00"),
            due_date=today + timedelta(days=3),
            status="Pending"
        ),
        Obligation(
            title="Racuni",
            amount=Decimal("900.00"),
            due_date=today + timedelta(days=5),
            status="Pending"
        ),
        Obligation(
            title="Kreditna rata",
            amount=Decimal("1500.00"),
            due_date=today + timedelta(days=6),
            status="Pending"
        )
    ]

    db.add_all(obligations)

    db.commit()


# ==========================================
# 3. IZVRSAVANJE AGENTA
# ==========================================

def run_demo():

    db = DemoSession()

    try:
        prepare_demo_data(db)

        agent = FinancialAgentRunner()

        print("\n====================================")
        print(" PERSONAL FINANCE AGENT")
        print(" DEMONSTRACIJSKI SCENARIO")
        print("====================================")

        print("\nDemonstracijski podaci su pripremljeni.")
        print("Glavna baza podataka nije mijenjana.")

        # SENSE
        financial_state = agent.sense(db)

        print("\n[1] SENSE - PRIKUPLJANJE PODATAKA")

        print(
            f"Trenutno stanje: "
            f"{financial_state['balance']:.2f} KM"
        )

        print(
            "Ocekivani prihodi:",
            financial_state["pending_income_count"]
        )

        print(
            "Neplacene obaveze:",
            financial_state["pending_obligation_count"]
        )

        # THINK
        analysis = agent.think(db, financial_state)

        print("\n[2] THINK - ANALIZA I PREDVIDJANJE")

        for prediction in analysis["income_predictions"]:

            print("\nIzvor prihoda:", prediction["source"])
            print("Ocekivani datum:", prediction["expected_date"])
            print("Predvidjeni datum:", prediction["predicted_date"])
            print("Prosjecno kasnjenje:", prediction["average_delay"])
            print("Historijskih uplata:", prediction["sample_count"])
            print("Pouzdanost:", prediction["confidence"])

        cashflow = analysis["cashflow"]

        print("\nHronoloska simulacija novcanog toka:")

        for event in cashflow["timeline"]:

            print(
                f"{event['date']} | "
                f"{event['type']} | "
                f"{event['description']} | "
                f"Iznos: {event['amount']:.2f} KM | "
                f"Stanje: {event['balance']:.2f} KM"
            )

        if cashflow["has_shortage"]:

            print("\nPrvi manjak:", cashflow["first_shortage_date"])

            print(
                "Najveci manjak:",
                f"{cashflow['maximum_shortage']:.2f} KM"
            )

            risk = analysis["risk"]

            print("Nivo rizika:", risk["risk_level"])
            print("Vrijeme za reakciju:", risk["days_remaining"], "dana")
            print("Preporuka:", risk["recommendation"])

        else:
            print("\nNije predvidjen manjak novca.")

        # ACT
        decision = agent.act(db, analysis)

        print("\n[3] ACT - ODLUKA AGENTA")

        if decision["alert_created"]:
            print("Novo upozorenje je kreirano!")

        elif decision.get("alert_updated"):
            print("Postojece upozorenje je azurirano!")

        else:
            print("Nije kreirano novo upozorenje.")

        print("\nPoruka agenta:")
        print(decision["message"])

        # LEARN
        learned_sources = agent.learn(db)

        print("\n[4] LEARN - HISTORIJSKO ISKUSTVO")

        for source, delays in learned_sources.items():

            average_delay = sum(delays) / len(delays)

            print(
                f"{source}: {len(delays)} uplata, "
                f"prosjecno kasnjenje "
                f"{average_delay:.2f} dana"
            )

        print("\n====================================")
        print(" DEMONSTRACIJA ZAVRSENA")
        print("====================================")

    finally:
        db.close()
        demo_engine.dispose()


if __name__ == "__main__":
    run_demo()
