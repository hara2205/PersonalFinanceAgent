
from decimal import Decimal

from app.models import AccountState, IncomePayment, Obligation
from app.income_prediction import predict_income_date


def analyze_cashflow(db):
    """
    Analizira buduci novcani tok na osnovu:
    - trenutnog stanja racuna
    - ocekivanih prihoda
    - unaprijed evidentiranih buducih uplata
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

    # 1. Ocekivani prihodi
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

    # 2. Buduce uplate koje su vec evidentirane
    scheduled_incomes = (
        db.query(IncomePayment)
        .filter(
            IncomePayment.status == "ScheduledReceived"
        )
        .all()
    )

    for income in scheduled_incomes:
        events.append({
            "date": income.actual_date,
            "priority": 1,
            "type": "income",
            "description": income.source_name,
            "amount": Decimal(income.actual_amount)
        })

    # 3. Neplacene obaveze
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

    # 4. Hronolosko sortiranje
    # Obaveza se obradjuje prije prihoda istog dana.
    events.sort(
        key=lambda event: (
            event["date"],
            event["priority"]
        )
    )

    timeline = []
    first_shortage_date = None
    maximum_shortage = Decimal("0.00")

    # 5. Simulacija novcanog toka
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
