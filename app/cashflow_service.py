
from decimal import Decimal

from app.database import SessionLocal
from app.models import AccountState, IncomePayment, Obligation
from app.income_prediction import predict_income_date


def analyze_cashflow(db):
    """
    Analizira buduci novcani tok na osnovu:
    - trenutnog stanja racuna
    - ocekivanih prihoda
    - predvidjenih datuma prihoda
    - neplacenih finansijskih obaveza
    """

    account = (
        db.query(AccountState)
        .order_by(AccountState.id)
        .first()
    )

    if account is None:
        raise ValueError("Trenutno stanje racuna nije uneseno.")

    balance = Decimal(account.current_balance)

    events = []

    # --------------------------------------
    # 1. DODAVANJE OCEKIVANIH PRIHODA
    # --------------------------------------

    pending_incomes = (
        db.query(IncomePayment)
        .filter(IncomePayment.status == "Expected")
        .all()
    )

    for income in pending_incomes:
        prediction = predict_income_date(db, income)

        events.append({
            "date": prediction["predicted_date"],
            "priority": 1,
            "type": "income",
            "description": income.source_name,
            "amount": Decimal(income.expected_amount)
        })

    # --------------------------------------
    # 2. DODAVANJE NEPLACENIH OBAVEZA
    # --------------------------------------

    pending_obligations = (
        db.query(Obligation)
        .filter(Obligation.status == "Pending")
        .all()
    )

    for obligation in pending_obligations:
        events.append({
            "date": obligation.due_date,
            "priority": 0,
            "type": "obligation",
            "description": obligation.title,
            "amount": Decimal(obligation.amount)
        })

    # --------------------------------------
    # 3. HRONOLOSKO SORTIRANJE DOGADJAJA
    # --------------------------------------

    # Ako prihod i obaveza imaju isti datum,
    # prvo obradjujemo obavezu.
    events.sort(
        key=lambda event: (
            event["date"],
            event["priority"]
        )
    )

    timeline = []

    first_shortage_date = None
    maximum_shortage = Decimal("0.00")

    # --------------------------------------
    # 4. SIMULACIJA NOVCANOG TOKA
    # --------------------------------------

    for event in events:

        if event["type"] == "income":
            balance += event["amount"]
            event_name = "PRIHOD"

        else:
            balance -= event["amount"]
            event_name = "OBAVEZA"

        timeline.append({
            "date": event["date"],
            "type": event_name,
            "description": event["description"],
            "amount": event["amount"],
            "balance": balance
        })

        # Evidentiramo prvi datum kada novac nije dovoljan.
        if balance < 0:
            if first_shortage_date is None:
                first_shortage_date = event["date"]

            current_shortage = abs(balance)

            if current_shortage > maximum_shortage:
                maximum_shortage = current_shortage

    return {
        "starting_balance": Decimal(account.current_balance),
        "final_balance": balance,
        "first_shortage_date": first_shortage_date,
        "maximum_shortage": maximum_shortage,
        "has_shortage": first_shortage_date is not None,
        "timeline": timeline
    }


def main():
    db = SessionLocal()

    try:
        result = analyze_cashflow(db)

        print("====================================")
        print(" ANALIZA NOVCANOG TOKA")
        print("====================================")

        print(
            f"\nPocetno stanje: "
            f"{result['starting_balance']:.2f} KM"
        )

        print("\nHRONOLOSKI PREGLED:")

        for event in result["timeline"]:
            print(
                f"{event['date']} | "
                f"{event['type']} | "
                f"{event['description']} | "
                f"{event['amount']:.2f} KM | "
                f"Stanje: {event['balance']:.2f} KM"
            )

        print("\n====================================")

        if result["has_shortage"]:
            print("UPOZORENJE: PREDVIDJEN MANJAK NOVCA!")
            print(
                "Datum prvog manjka:",
                result["first_shortage_date"]
            )
            print(
                "Najveci predvidjeni manjak:",
                f"{result['maximum_shortage']:.2f} KM"
            )
        else:
            print("Nije predvidjen manjak novca.")

        print(
            f"Zavrsno stanje: "
            f"{result['final_balance']:.2f} KM"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
