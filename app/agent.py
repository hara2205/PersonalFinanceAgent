from datetime import date, datetime, timezone

from app.database import SessionLocal
from app.models import AccountState, IncomePayment, Obligation
from app.income_prediction import predict_income_date
from app.cashflow_service import analyze_cashflow
from app.decisions import make_agent_decision, assess_risk


class FinancialAgentRunner:
    """
    Centralna klasa finansijskog agenta.

    Povezuje cetiri faze:
    Sense -> Think -> Act -> Learn
    """

    def sense(self, db):
        """Prikuplja trenutno finansijsko stanje."""

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

        scheduled_incomes = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.status == "ScheduledReceived"
            )
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
            "scheduled_income_count": len(scheduled_incomes),
            "pending_obligation_count": len(pending_obligations),
            "pending_incomes": pending_incomes,
            "scheduled_incomes": scheduled_incomes,
            "pending_obligations": pending_obligations
        }

    def think(self, db, financial_state, reference_date: date | None = None):
        """
        Analizira prihode, novcani tok
        i nivo finansijskog rizika uz jedinstveni referentni datum.
        """
        current_date = reference_date or date.today()
        income_predictions = []

        for income in financial_state["pending_incomes"]:
            prediction = predict_income_date(db, income, reference_date=current_date)
            income_predictions.append(prediction)

        cashflow = analyze_cashflow(db, reference_date=current_date)

        risk = None

        if cashflow["has_shortage"]:

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

            risk = assess_risk(
                cashflow["first_shortage_date"],
                first_shortage_amount,
                cashflow["maximum_shortage"],
                reference_date=current_date
            )

        return {
            "reference_date": current_date,
            "income_predictions": income_predictions,
            "cashflow": cashflow,
            "risk": risk
        }

    def act(self, db, analysis, reference_date: date | None = None):
        """
        Donosi odluku koristeci vec izvrsenu analizu i referentni datum.
        """
        current_date = reference_date or analysis.get("reference_date") or date.today()
        return make_agent_decision(
            db,
            cashflow_result=analysis["cashflow"],
            reference_date=current_date
        )

    def learn(self, db):
        """
        Uci iz stvarno primljenih historijskih uplata.

        Buduce zakazane uplate ne koriste se za ucenje.
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

    def step(self, reference_date: date | None = None):
        """Izvrsava jedan kompletan ciklus agenta."""

        db = SessionLocal()
        current_date = reference_date or date.today()

        try:
            execution_time = datetime.now(timezone.utc)

            # 1. SENSE
            financial_state = self.sense(db)

            # 2. THINK
            analysis = self.think(db, financial_state, reference_date=current_date)

            # 3. ACT
            decision = self.act(db, analysis, reference_date=current_date)

            # 4. LEARN
            learned_sources = self.learn(db)

            return {
                "execution_time": execution_time,
                "reference_date": current_date,
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