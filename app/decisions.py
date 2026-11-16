
from decimal import Decimal

from app.database import SessionLocal
from app.models import AgentAlert, IncomePayment
from app.cashflow_service import analyze_cashflow
from app.income_prediction import predict_income_date


def calculate_confidence(db):
    """
    Racuna heuristicki indeks pouzdanosti
    na osnovu kolicine historijskih podataka.

    Ovo nije statisticki kalibrisana vjerovatnoca.
    """

    pending_incomes = (
        db.query(IncomePayment)
        .filter(IncomePayment.status == "Expected")
        .all()
    )

    if not pending_incomes:
        return Decimal("0.2500")

    scores = []

    for income in pending_incomes:
        prediction = predict_income_date(db, income)
        sample_count = prediction["sample_count"]

        if sample_count == 0:
            score = 0.25
        elif sample_count < 3:
            score = 0.45
        elif sample_count < 6:
            score = 0.65
        else:
            score = 0.80

        scores.append(score)

    return Decimal(str(min(scores))).quantize(
        Decimal("0.0001")
    )


def make_agent_decision(db):
    """
    Analizira novcani tok i odlucuje
    da li treba generisati upozorenje.
    """

    result = analyze_cashflow(db)

    if not result["has_shortage"]:
        # Ako vise nema rizika, deaktiviramo
        # prethodna aktivna upozorenja.
        active_alerts = (
            db.query(AgentAlert)
            .filter(AgentAlert.is_active == True)
            .all()
        )

        for alert in active_alerts:
            alert.is_active = False

        db.commit()

        return {
            "alert_created": False,
            "message": "Nije predvidjen manjak novca."
        }

    shortage_date = result["first_shortage_date"]
    shortage_amount = result["maximum_shortage"]

    # Pronalazimo obavezu koja je izazvala
    # prvi negativan saldo.
    affected_event = next(
        (
            event
            for event in result["timeline"]
            if event["balance"] < 0
            and event["date"] == shortage_date
        ),
        None
    )

    affected_obligation = (
        affected_event["description"]
        if affected_event
        else "Finansijska obaveza"
    )

    confidence = calculate_confidence(db)

    message = (
        f"Predvidjen je nedostatak novca dana "
        f"{shortage_date}. "
        f"Obaveza koja izaziva prvi manjak: "
        f"{affected_obligation}. "
        f"Predvidjeni manjak iznosi "
        f"{shortage_amount:.2f} KM. "
        f"Preporucuje se da korisnik obezbijedi "
        f"dodatna sredstva ili provjeri rok placanja."
    )

    # Provjeravamo postoji li vec aktivno
    # upozorenje za isti datum.
    existing_alert = (
        db.query(AgentAlert)
        .filter(
            AgentAlert.shortage_date == shortage_date,
            AgentAlert.is_active == True
        )
        .first()
    )

    if existing_alert:
        # Azuriramo postojece upozorenje
        # umjesto kreiranja duplikata.
        existing_alert.shortage_amount = shortage_amount
        existing_alert.message = message
        existing_alert.confidence = confidence

        db.commit()

        return {
            "alert_created": False,
            "alert_updated": True,
            "message": message,
            "shortage_date": shortage_date,
            "shortage_amount": shortage_amount,
            "confidence": confidence
        }

    # Kreiramo novo upozorenje.
    alert = AgentAlert(
        shortage_date=shortage_date,
        shortage_amount=shortage_amount,
        message=message,
        confidence=confidence,
        is_active=True
    )

    db.add(alert)
    db.commit()

    return {
        "alert_created": True,
        "alert_updated": False,
        "message": message,
        "shortage_date": shortage_date,
        "shortage_amount": shortage_amount,
        "confidence": confidence
    }


def main():
    db = SessionLocal()

    try:
        decision = make_agent_decision(db)

        print("====================================")
        print(" ODLUKA FINANSIJSKOG AGENTA")
        print("====================================")

        if decision["alert_created"]:
            print("Novo upozorenje je kreirano!")

        elif decision.get("alert_updated"):
            print("Postojece upozorenje je azurirano!")

        else:
            print("Nije kreirano novo upozorenje.")

        print("\nPoruka agenta:")
        print(decision["message"])

        if decision.get("shortage_date"):
            print("\nDatum manjka:", decision["shortage_date"])
            print(
                "Iznos manjka:",
                f"{decision['shortage_amount']:.2f} KM"
            )
            print(
                "Indeks pouzdanosti:",
                f"{decision['confidence']:.2f}"
            )

        print("\nBroj upozorenja u bazi:",
              db.query(AgentAlert).count())

        print("Broj aktivnih upozorenja:",
              db.query(AgentAlert)
              .filter(AgentAlert.is_active == True)
              .count())

    finally:
        db.close()


if __name__ == "__main__":
    main()
