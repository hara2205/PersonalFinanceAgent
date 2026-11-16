
from datetime import date
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


def assess_risk(shortage_date, first_shortage_amount, maximum_shortage):
    """
    Procjenjuje nivo finansijskog rizika.

    Procjena se zasniva na vremenu do manjka
    i iznosima predvidjenog manjka.
    """

    days_remaining = (shortage_date - date.today()).days

    first_shortage_amount = Decimal(str(first_shortage_amount))
    maximum_shortage = Decimal(str(maximum_shortage))

    if (
        days_remaining <= 3
        or maximum_shortage >= Decimal("1000")
    ):
        risk_level = "HIGH"
        recommendation = (
            "Potrebno je hitno reagovati. "
            "Provjerite mogucnost odlaganja obaveze "
            "ili obezbjedjivanja dodatnih sredstava."
        )

    elif (
        days_remaining <= 7
        or first_shortage_amount >= Decimal("300")
    ):
        risk_level = "MEDIUM"
        recommendation = (
            "Preporucuje se planiranje dodatnih sredstava "
            "i provjera rokova placanja obaveza."
        )

    else:
        risk_level = "LOW"
        recommendation = (
            "Situacija trenutno nije hitna, ali se "
            "preporucuje pracenje buduceg novcanog toka."
        )

    return {
        "risk_level": risk_level,
        "days_remaining": days_remaining,
        "recommendation": recommendation
    }


def make_agent_decision(db, cashflow_result=None):
    """
    Analizira novcani tok i donosi odluku o upozorenju.

    Ako je analiza novcanog toka vec izvrsena,
    koristi se postojeci rezultat umjesto ponovnog racunanja.
    """

    if cashflow_result is None:
        result = analyze_cashflow(db)
    else:
        result = cashflow_result

    # --------------------------------------
    # 1. NEMA PREDVIDJENOG MANJKA
    # --------------------------------------

    if not result["has_shortage"]:

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
            "alert_updated": False,
            "risk_level": "NONE",
            "message": "Nije predvidjen manjak novca."
        }

    # --------------------------------------
    # 2. ANALIZA PRVOG I NAJVECEG MANJKA
    # --------------------------------------

    shortage_date = result["first_shortage_date"]
    maximum_shortage = Decimal(str(result["maximum_shortage"]))

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

    first_shortage_amount = (
        abs(Decimal(str(affected_event["balance"])))
        if affected_event
        else maximum_shortage
    )

    # --------------------------------------
    # 3. PROCJENA RIZIKA
    # --------------------------------------

    risk = assess_risk(
        shortage_date,
        first_shortage_amount,
        maximum_shortage
    )

    confidence = calculate_confidence(db)

    risk_labels = {
        "LOW": "NIZAK",
        "MEDIUM": "SREDNJI",
        "HIGH": "VISOK"
    }

    # --------------------------------------
    # 4. GENERISANJE PORUKE
    # --------------------------------------

    message = (
        f"PROCJENJENI FINANSIJSKI RIZIK: "
        f"{risk_labels[risk['risk_level']]}. "
        f"Prvi nedostatak novca predvidjen je za "
        f"{shortage_date}. "
        f"Vrijeme za reakciju: "
        f"{risk['days_remaining']} dana. "
        f"Obaveza koja izaziva prvi manjak: "
        f"{affected_obligation}. "
        f"Tada ce nedostajati "
        f"{first_shortage_amount:.2f} KM. "
        f"Najveci predvidjeni manjak iznosi "
        f"{maximum_shortage:.2f} KM. "
        f"PREPORUKA AGENTA: "
        f"{risk['recommendation']}"
    )

    # --------------------------------------
    # 5. PROVJERA POSTOJECEG UPOZORENJA
    # --------------------------------------

    existing_alert = (
        db.query(AgentAlert)
        .filter(
            AgentAlert.shortage_date == shortage_date,
            AgentAlert.is_active == True
        )
        .first()
    )

    if existing_alert:

        existing_alert.shortage_amount = maximum_shortage
        existing_alert.message = message
        existing_alert.confidence = confidence

        db.commit()

        return {
            "alert_created": False,
            "alert_updated": True,
            "risk_level": risk["risk_level"],
            "days_remaining": risk["days_remaining"],
            "message": message,
            "shortage_date": shortage_date,
            "shortage_amount": maximum_shortage,
            "first_shortage_amount": first_shortage_amount,
            "confidence": confidence,
            "recommendation": risk["recommendation"]
        }

    # --------------------------------------
    # 6. KREIRANJE NOVOG UPOZORENJA
    # --------------------------------------

    alert = AgentAlert(
        shortage_date=shortage_date,
        shortage_amount=maximum_shortage,
        message=message,
        confidence=confidence,
        is_active=True
    )

    db.add(alert)
    db.commit()

    return {
        "alert_created": True,
        "alert_updated": False,
        "risk_level": risk["risk_level"],
        "days_remaining": risk["days_remaining"],
        "message": message,
        "shortage_date": shortage_date,
        "shortage_amount": maximum_shortage,
        "first_shortage_amount": first_shortage_amount,
        "confidence": confidence,
        "recommendation": risk["recommendation"]
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

            print("\nNivo rizika:", decision["risk_level"])
            print("Vrijeme za reakciju:", decision["days_remaining"], "dana")
            print("Datum prvog manjka:", decision["shortage_date"])

            print(
                "Manjak kod prve obaveze:",
                f"{decision['first_shortage_amount']:.2f} KM"
            )

            print(
                "Najveci predvidjeni manjak:",
                f"{decision['shortage_amount']:.2f} KM"
            )

            print(
                "Indeks pouzdanosti:",
                f"{decision['confidence']:.2f}"
            )

            print("Preporuka:", decision["recommendation"])

        print("\nBroj upozorenja u bazi:",
              db.query(AgentAlert).count())

        print(
            "Broj aktivnih upozorenja:",
            db.query(AgentAlert)
            .filter(AgentAlert.is_active == True)
            .count()
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
