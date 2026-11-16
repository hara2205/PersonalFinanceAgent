
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import FinancialAgentRunner
from app.database import SessionLocal
from app.models import (
    AccountState,
    IncomePayment,
    Obligation,
    AgentAlert
)
from app.cashflow_service import analyze_cashflow


# Agent se izvrsava jednom dnevno.
AGENT_INTERVAL = 24 * 60 * 60

agent = FinancialAgentRunner()
agent_lock = asyncio.Lock()


# Podaci koje korisnik salje prilikom evidentiranja prihoda.
class ReceiveIncomeRequest(BaseModel):
    actual_date: date
    actual_amount: Decimal = Field(gt=0)


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
    """Vraca pregled trenutnog finansijskog stanja."""

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


@app.get("/finance/forecast")
def get_financial_forecast():
    """Vraca hronolosku projekciju buduceg novcanog toka."""

    db = SessionLocal()

    try:
        result = analyze_cashflow(db)

        return {
            "starting_balance": float(result["starting_balance"]),
            "final_balance": float(result["final_balance"]),
            "has_shortage": result["has_shortage"],
            "first_shortage_date": (
                result["first_shortage_date"].isoformat()
                if result["first_shortage_date"]
                else None
            ),
            "maximum_shortage": float(result["maximum_shortage"]),
            "timeline": [
                {
                    "date": event["date"].isoformat(),
                    "type": event["type"],
                    "description": event["description"],
                    "amount": float(event["amount"]),
                    "balance": float(event["balance"])
                }
                for event in result["timeline"]
            ]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Greska prilikom analize novcanog toka: {str(error)}"
        )

    finally:
        db.close()


@app.post("/incomes/{income_id}/receive")
def receive_income(
    income_id: int,
    request: ReceiveIncomeRequest
):
    """
    Evidentira stvarno primljeni prihod,
    azurira stanje racuna i cuva podatke za ucenje agenta.
    """

    db = SessionLocal()

    try:
        income = (
            db.query(IncomePayment)
            .filter(IncomePayment.id == income_id)
            .first()
        )

        if income is None:
            raise HTTPException(
                status_code=404,
                detail="Prihod nije pronadjen."
            )

        if income.status != "Expected":
            raise HTTPException(
                status_code=409,
                detail="Ovaj prihod je vec evidentiran kao primljen."
            )

        account = (
            db.query(AccountState)
            .order_by(AccountState.id)
            .first()
        )

        if account is None:
            raise HTTPException(
                status_code=404,
                detail="Finansijsko stanje racuna nije pronadjeno."
            )

        # Evidentiranje stvarnih podataka o uplati.
        income.actual_date = request.actual_date
        income.actual_amount = request.actual_amount
        income.status = "Received"

        # Uvecavanje trenutnog stanja racuna.
        account.current_balance = (
            Decimal(account.current_balance)
            + request.actual_amount
        )

        # Trajno cuvanje promjena u bazi.
        db.commit()
        db.refresh(income)
        db.refresh(account)

        delay_days = (
            income.actual_date - income.expected_date
        ).days

        return {
            "status": "success",
            "message": "Prihod je uspjesno evidentiran.",
            "income": {
                "id": income.id,
                "source": income.source_name,
                "expected_date": income.expected_date.isoformat(),
                "actual_date": income.actual_date.isoformat(),
                "expected_amount": float(income.expected_amount),
                "actual_amount": float(income.actual_amount),
                "delay_days": delay_days,
                "status": income.status
            },
            "new_account_balance": float(account.current_balance)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Greska prilikom evidentiranja prihoda: {str(error)}"
        )

    finally:
        db.close()
