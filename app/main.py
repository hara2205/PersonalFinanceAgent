
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.agent import FinancialAgentRunner
from app.database import SessionLocal
from app.models import (
    AccountState,
    IncomePayment,
    Obligation,
    AgentAlert
)


# Agent se izvrsava jednom dnevno.
AGENT_INTERVAL = 24 * 60 * 60

agent = FinancialAgentRunner()
agent_lock = asyncio.Lock()


async def run_agent_once():
    """Pokrece jedan ciklus finansijskog agenta."""

    async with agent_lock:
        result = await asyncio.to_thread(agent.step)
        return result


async def periodic_agent_runner():
    """Automatsko izvrsavanje agenta svakih 24 sata."""

    while True:
        try:
            print("\n[BACKGROUND] Pokretanje automatske analize...")

            await run_agent_once()

            print("[BACKGROUND] Analiza je zavrsena.")

        except Exception as error:
            print(
                "[BACKGROUND] Greska prilikom izvrsavanja agenta:",
                error
            )

        await asyncio.sleep(AGENT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pokretanje i zaustavljanje pozadinskog agenta."""

    print("\n====================================")
    print(" POKRETANJE PERSONAL FINANCE BACKEND-a")
    print("====================================")

    background_task = asyncio.create_task(
        periodic_agent_runner()
    )

    yield

    background_task.cancel()

    try:
        await background_task
    except asyncio.CancelledError:
        print("\n[BACKGROUND] Agent je zaustavljen.")

    print("[BACKEND] Aplikacija je ugasena.")


app = FastAPI(
    title="Personal Finance Agent API",
    description=(
        "API za pracenje finansijskih obaveza, "
        "predvidjanje prihoda i analizu likvidnosti."
    ),
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {
        "application": "Personal Finance Agent",
        "status": "running",
        "message": "Backend aplikacija je aktivna."
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/agent/run")
async def run_agent_manually():
    """Rucno pokretanje jednog ciklusa agenta."""

    try:
        result = await run_agent_once()

        return {
            "status": "success",
            "message": "Agent je uspjesno izvrsio analizu.",
            "execution_time": result["execution_time"].isoformat(),
            "decision": {
                "alert_created": result["decision"]["alert_created"],
                "alert_updated": result["decision"].get(
                    "alert_updated", False
                ),
                "message": result["decision"]["message"]
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Greska prilikom izvrsavanja agenta: {str(error)}"
        )


@app.get("/finance/overview")
def get_financial_overview():
    """
    Vraca pregled trenutnog finansijskog stanja,
    ocekivanih prihoda i neplacenih obaveza.
    """

    db = SessionLocal()

    try:
        account = db.query(AccountState).first()

        incomes = (
            db.query(IncomePayment)
            .filter(IncomePayment.status == "Expected")
            .order_by(IncomePayment.expected_date)
            .all()
        )

        obligations = (
            db.query(Obligation)
            .filter(Obligation.status == "Pending")
            .order_by(Obligation.due_date)
            .all()
        )

        active_alerts_count = (
            db.query(AgentAlert)
            .filter(AgentAlert.is_active == True)
            .count()
        )

        return {
            "current_balance": (
                float(account.current_balance)
                if account else 0.0
            ),
            "expected_incomes": [
                {
                    "id": income.id,
                    "source": income.source_name,
                    "expected_date": income.expected_date.isoformat(),
                    "expected_amount": float(income.expected_amount)
                }
                for income in incomes
            ],
            "pending_obligations": [
                {
                    "id": obligation.id,
                    "title": obligation.title,
                    "due_date": obligation.due_date.isoformat(),
                    "amount": float(obligation.amount)
                }
                for obligation in obligations
            ],
            "active_alerts_count": active_alerts_count
        }

    finally:
        db.close()


@app.get("/alerts")
def get_active_alerts():
    """Vraca sva trenutno aktivna upozorenja agenta."""

    db = SessionLocal()

    try:
        alerts = (
            db.query(AgentAlert)
            .filter(AgentAlert.is_active == True)
            .order_by(AgentAlert.created_at.desc())
            .all()
        )

        return {
            "total": len(alerts),
            "alerts": [
                {
                    "id": alert.id,
                    "created_at": alert.created_at.isoformat(),
                    "shortage_date": (
                        alert.shortage_date.isoformat()
                        if alert.shortage_date else None
                    ),
                    "shortage_amount": float(alert.shortage_amount),
                    "message": alert.message,
                    "confidence": alert.confidence,
                    "is_active": alert.is_active
                }
                for alert in alerts
            ]
        }

    finally:
        db.close()
