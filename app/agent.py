
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import AccountState, IncomePayment, Obligation
from app.income_prediction import predict_income_date
from app.cashflow_service import analyze_cashflow
from app.decisions import make_agent_decision


class FinancialAgentRunner:
    """
    Centralna klasa finansijskog agenta.

    Povezuje cetiri faze:
    Sense -> Think -> Act -> Learn
    """

    def sense(self, db):
        """
        Prikuplja trenutno finansijsko stanje.
        """

        account = (
            db.query(AccountState)
            .order_by(AccountState.id)
            .first()
        )

        if account is None:
            raise ValueError(
                "Stanje racuna nije uneseno u bazu."
            )

        pending_incomes = (
            db.query(IncomePayment)
            .filter(IncomePayment.status == "Expected")
            .all()
        )

        pending_obligations = (
            db.query(Obligation)
            .filter(Obligation.status == "Pending")
            .all()
        )

        return {
            "balance": account.current_balance,
            "pending_income_count": len(pending_incomes),
            "pending_obligation_count": len(pending_obligations),
            "pending_incomes": pending_incomes,
            "pending_obligations": pending_obligations
        }

    def think(self, db, financial_state):
        """
        Analizira prihode i buduce novcane tokove.
        """

        income_predictions = []

        for income in financial_state["pending_incomes"]:
            prediction = predict_income_date(db, income)
            income_predictions.append(prediction)

        cashflow = analyze_cashflow(db)

        return {
            "income_predictions": income_predictions,
            "cashflow": cashflow
        }

    def act(self, db, analysis):
        """
        Donosi odluku o kreiranju ili azuriranju upozorenja.
        """

        return make_agent_decision(db)

    def learn(self, db):
        """
        Analizira historijska iskustva o kasnjenju prihoda.

        Prediktor koristi evidentirane stvarne uplate
        za prilagodjavanje buducih predvidjanja.
        """

        received_payments = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.status == "Received",
                IncomePayment.actual_date.isnot(None)
            )
            .all()
        )

        learned_sources = {}

        for payment in received_payments:
            delay = (
                payment.actual_date - payment.expected_date
            ).days

            source = payment.source_name

            if source not in learned_sources:
                learned_sources[source] = []

            learned_sources[source].append(delay)

        return learned_sources

    def step(self):
        """
        Izvrsava jedan kompletan ciklus agenta.
        """

        db = SessionLocal()

        try:
            execution_time = datetime.now(timezone.utc)

            print("\n====================================")
            print(" PERSONAL FINANCE AGENT")
            print("====================================")

            # ==================================
            # 1. SENSE - PRIKUPLJANJE PODATAKA
            # ==================================

            financial_state = self.sense(db)

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

            # ==================================
            # 2. THINK - ANALIZA I PREDVIDJANJE
            # ==================================

            analysis = self.think(db, financial_state)

            print("\n[2] THINK - ANALIZA I PREDVIDJANJE")

            for prediction in analysis["income_predictions"]:
                print(
                    f"{prediction['source']}: "
                    f"ocekivano {prediction['expected_date']}, "
                    f"predvidjeno {prediction['predicted_date']}"
                )

            cashflow = analysis["cashflow"]

            if cashflow["has_shortage"]:

                # Pronalazimo dogadjaj koji izaziva
                # prvi negativan saldo.
                first_shortage_event = next(
                    (
                        event
                        for event in cashflow["timeline"]
                        if event["balance"] < 0
                        and event["date"] == cashflow["first_shortage_date"]
                    ),
                    None
                )

                first_shortage_amount = (
                    abs(first_shortage_event["balance"])
                    if first_shortage_event
                    else cashflow["maximum_shortage"]
                )

                print(
                    "Datum prvog manjka:",
                    cashflow["first_shortage_date"]
                )

                print(
                    "Manjak nakon prve obaveze:",
                    f"{first_shortage_amount:.2f} KM"
                )

                print(
                    "Najveci predvidjeni manjak:",
                    f"{cashflow['maximum_shortage']:.2f} KM"
                )

            else:
                print("Nije predvidjen manjak novca.")

            # ==================================
            # 3. ACT - DONOSENJE ODLUKE
            # ==================================

            decision = self.act(db, analysis)

            print("\n[3] ACT - ODLUKA AGENTA")

            if decision["alert_created"]:
                print("Novo upozorenje je kreirano!")

            elif decision.get("alert_updated"):
                print("Postojece upozorenje je azurirano!")

            else:
                print("Nije kreirano novo upozorenje.")

            print("\nPoruka agenta:")
            print(decision["message"])

            # ==================================
            # 4. LEARN - ANALIZA ISKUSTVA
            # ==================================

            learned_sources = self.learn(db)

            print("\n[4] LEARN - HISTORIJSKO ISKUSTVO")

            if not learned_sources:
                print("Nema historijskih uplata za analizu.")

            for source, delays in learned_sources.items():

                average_delay = sum(delays) / len(delays)

                print(
                    f"{source}: {len(delays)} uplata, "
                    f"prosjecno kasnjenje "
                    f"{average_delay:.2f} dana"
                )

            # ==================================
            # ZAVRSETAK CIKLUSA
            # ==================================

            print("\nVrijeme izvrsavanja:", execution_time)
            print("====================================")

            return {
                "execution_time": execution_time,
                "financial_state": financial_state,
                "analysis": analysis,
                "decision": decision,
                "learned_sources": learned_sources
            }

        finally:
            db.close()


if __name__ == "__main__":
    agent = FinancialAgentRunner()
    agent.step()
