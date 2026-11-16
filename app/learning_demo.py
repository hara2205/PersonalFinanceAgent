
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import AccountState, IncomePayment, Obligation
from app.agent import FinancialAgentRunner


# ==========================================
# 1. ODVOJENA DEMONSTRACIJSKA BAZA
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_URL = (
    f"sqlite:///{DATABASE_DIR / 'demo_learning_comparison.db'}"
)

demo_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

DemoSession = sessionmaker(
    bind=demo_engine,
    autoflush=False,
    autocommit=False
)


# ==========================================
# 2. PRIPREMA ISTOG FINANSIJSKOG SCENARIJA
# ==========================================

def prepare_financial_scenario(db):
    """
    Priprema pocetno stanje, ocekivanu platu
    i racun koji dospijeva prije zakasnjele plate.
    """

    today = date.today()

    account = AccountState(
        current_balance=Decimal("1000.00")
    )

    expected_salary = IncomePayment(
        source_name="Plata",
        expected_date=today + timedelta(days=4),
        expected_amount=Decimal("1500.00"),
        status="Expected"
    )

    bill = Obligation(
        title="Racun za placanje",
        amount=Decimal("1200.00"),
        due_date=today + timedelta(days=5),
        status="Pending"
    )

    db.add_all([
        account,
        expected_salary,
        bill
    ])

    db.commit()
    db.refresh(expected_salary)

    return expected_salary


# ==========================================
# 3. PRIKAZ REZULTATA AGENTA
# ==========================================

def display_agent_result(agent, db, title):
    """
    Izvrsava Sense, Think i Act faze
    i prikazuje rezultat finansijske analize.
    """

    print("\n" + "=" * 55)
    print(title)
    print("=" * 55)

    financial_state = agent.sense(db)
    analysis = agent.think(db, financial_state)

    prediction = analysis["income_predictions"][0]
    cashflow = analysis["cashflow"]

    print("\nPREDVIDJANJE PRIHODA")
    print("Izvor:", prediction["source"])
    print("Ocekivani datum:", prediction["expected_date"])
    print("Predvidjeni datum:", prediction["predicted_date"])
    print("Prosjecno kasnjenje:", prediction["average_delay"], "dana")
    print("Broj historijskih uplata:", prediction["sample_count"])

    print("\nSIMULACIJA NOVCANOG TOKA")

    for event in cashflow["timeline"]:
        print(
            f"{event['date']} | "
            f"{event['description']} | "
            f"Iznos: {event['amount']:.2f} KM | "
            f"Stanje: {event['balance']:.2f} KM"
        )

    if cashflow["has_shortage"]:
        print("\nPredvidjeni prvi manjak:", cashflow["first_shortage_date"])
        print(
            "Najveci predvidjeni manjak:",
            f"{cashflow['maximum_shortage']:.2f} KM"
        )
    else:
        print("\nNije predvidjen manjak novca.")

    decision = agent.act(db, analysis)

    print("\nODLUKA AGENTA")
    print(decision["message"])

    if decision.get("alert_created"):
        print("Agent je samostalno kreirao novo upozorenje.")

    elif decision.get("alert_updated"):
        print("Postojece upozorenje je azurirano.")

    else:
        print("Nije kreirano novo upozorenje.")

    return {
        "prediction": prediction,
        "cashflow": cashflow,
        "decision": decision
    }


# ==========================================
# 4. DODAVANJE NOVOG ISKUSTVA
# ==========================================

def add_historical_experience(db):
    """
    Agent dobija tri prethodne uplate plate.
    Svaka od njih kasnila je tri dana.
    """

    today = date.today()

    for index in range(3):
        expected_date = today - timedelta(days=60 - index * 10)
        actual_date = expected_date + timedelta(days=3)

        payment = IncomePayment(
            source_name="Plata",
            expected_date=expected_date,
            expected_amount=Decimal("1500.00"),
            actual_date=actual_date,
            actual_amount=Decimal("1500.00"),
            status="Received"
        )

        db.add(payment)

    db.commit()

    print("\nAGENT JE DOBIO NOVO HISTORIJSKO ISKUSTVO")
    print("Broj novih historijskih uplata: 3")
    print("Zabiljezeno kasnjenje svake uplate: 3 dana")


# ==========================================
# 5. GLAVNA DEMONSTRACIJA
# ==========================================

def demonstrate_learning_comparison():
    # Ova baza se resetuje pri svakom pokretanju.
    Base.metadata.drop_all(bind=demo_engine)
    Base.metadata.create_all(bind=demo_engine)

    db = DemoSession()

    try:
        agent = FinancialAgentRunner()

        print("=" * 55)
        print(" PERSONAL FINANCE AGENT")
        print(" DEMONSTRACIJA ODLUKE PRIJE I POSLIJE UCENJA")
        print("=" * 55)

        print("\nKoristi se posebna demonstracijska baza.")
        print("Glavna baza podataka nije mijenjana.")

        # Isti pocetni finansijski scenario.
        prepare_financial_scenario(db)

        print("\nFINANSIJSKI PODACI U OBA SCENARIJA")
        print("Pocetno stanje: 1000.00 KM")
        print("Ocekivana plata: 1500.00 KM")
        print("Racun za placanje: 1200.00 KM")

        # PRVI PROLAZ: bez historije kasnjenja.
        before = display_agent_result(
            agent,
            db,
            "1. ODLUKA PRIJE UCENJA"
        )

        # Agent dobija prethodna iskustva.
        add_historical_experience(db)

        # DRUGI PROLAZ: sa naučenim obrascem kasnjenja.
        after = display_agent_result(
            agent,
            db,
            "2. ODLUKA NAKON UCENJA"
        )

        # Zavrsno poredjenje.
        print("\n" + "=" * 55)
        print("3. POREDJENJE REZULTATA")
        print("=" * 55)

        print(
            "\nPredvidjeni datum plate prije ucenja:",
            before["prediction"]["predicted_date"]
        )

        print(
            "Predvidjeni datum plate nakon ucenja:",
            after["prediction"]["predicted_date"]
        )

        print(
            "\nManjak prije ucenja:",
            before["cashflow"]["has_shortage"]
        )

        print(
            "Manjak nakon ucenja:",
            after["cashflow"]["has_shortage"]
        )

        print(
            "\nUpozorenje kreirano nakon ucenja:",
            after["decision"].get("alert_created", False)
        )

        print("\nGlavna baza podataka nije mijenjana.")
        print("Demonstracija je zavrsena.")

    finally:
        db.close()
        demo_engine.dispose()


if __name__ == "__main__":
    demonstrate_learning_comparison()
