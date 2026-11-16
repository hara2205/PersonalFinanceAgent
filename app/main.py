
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


AGENT_INTERVAL = 24 * 60 * 60

agent = FinancialAgentRunner()
agent_lock = asyncio.Lock()


class ReceiveIncomeRequest(BaseModel):
    actual_date: date
    actual_amount: Decimal = Field(gt=0)


def activate_due_incomes(simulation_date: date | None = None):
    """
    Aktivira unaprijed evidentirane uplate
    kada dodje njihov datum.

    Ako je proslijedjen simulation_date, koristi
    simulirani datum umjesto stvarnog datuma.
    """

    current_date = simulation_date or date.today()

    db = SessionLocal()

    try:
        due_incomes = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.status == "ScheduledReceived",
                IncomePayment.actual_date <= current_date
            )
            .all()
        )

        if not due_incomes:
            return 0

        account = (
            db.query(AccountState)
            .order_by(AccountState.id)
            .first()
        )

        if account is None:
            raise ValueError(
                "Finansijsko stanje racuna nije pronadjeno."
            )

        activated_count = 0

        for income in due_incomes:
            income.status = "Received"

            account.current_balance = (
                Decimal(account.current_balance)
                + Decimal(income.actual_amount)
            )

            activated_count += 1

        account.updated_at = datetime.now(timezone.utc)

        db.commit()

        print(
            f"[BACKGROUND] Aktivirano uplata: {activated_count}"
        )

        return activated_count

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


async def run_agent_once(simulation_date: date | None = None):
    """
    Aktivira dospjele buduce uplate, a zatim pokrece agenta.
    """

    async with agent_lock:

        activated_count = await asyncio.to_thread(
            activate_due_incomes,
            simulation_date
        )

        result = await asyncio.to_thread(agent.step)

        result["activated_income_count"] = activated_count

        return result


async def periodic_agent_runner():

    while True:

        try:
            print("\n[BACKGROUND] Pokretanje finansijske analize...")

            result = await run_agent_once()

            print(
                "[BACKGROUND] Aktivirano uplata:",
                result["activated_income_count"]
            )

            print("[BACKGROUND] Analiza je zavrsena.")

        except Exception as error:
            print(
                "[BACKGROUND] Greska:",
                error
            )

        await asyncio.sleep(AGENT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):

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
    version="1.2.0",
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
async def run_agent_manually(
    simulation_date: date | None = None
):

    try:
        result = await run_agent_once(simulation_date)

        return {
            "status": "success",
            "message": "Agent je uspjesno izvrsio analizu.",
            "simulation_date": (
                simulation_date or date.today()
            ).isoformat(),
            "activated_income_count": result[
                "activated_income_count"
            ],
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
            detail=(
                "Greska prilikom izvrsavanja agenta: "
                f"{str(error)}"
            )
        )


@app.get("/finance/overview")
def get_financial_overview():

    db = SessionLocal()

    try:
        account = db.query(AccountState).first()

        incomes = (
            db.query(IncomePayment)
            .filter(
                IncomePayment.status.in_([
                    "Expected",
                    "ScheduledReceived"
                ])
            )
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
                    "expected_amount": float(income.expected_amount),
                    "actual_date": (
                        income.actual_date.isoformat()
                        if income.actual_date else None
                    ),
                    "actual_amount": (
                        float(income.actual_amount)
                        if income.actual_amount is not None else None
                    ),
                    "status": income.status
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
                    "shortage_date": alert.shortage_date.isoformat(),
                    "shortage_amount": float(alert.shortage_amount),
                    "message": alert.message,
                    "confidence": float(alert.confidence),
                    "is_active": alert.is_active
                }
                for alert in alerts
            ]
        }

    finally:
        db.close()


@app.get("/finance/forecast")
def get_financial_forecast():

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
            detail=(
                "Greska prilikom analize novcanog toka: "
                f"{str(error)}"
            )
        )

    finally:
        db.close()


@app.post("/incomes/{income_id}/receive")
async def receive_income(
    income_id: int,
    request: ReceiveIncomeRequest
):

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
                detail="Ovaj prihod je vec evidentiran ili zakazan."
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

        income.actual_date = request.actual_date
        income.actual_amount = request.actual_amount

        if request.actual_date > date.today():

            income.status = "ScheduledReceived"

            message = (
                "Buduca uplata je evidentirana. "
                "Saldo ce biti azuriran na datum uplate."
            )

        else:

            income.status = "Received"

            account.current_balance = (
                Decimal(account.current_balance)
                + request.actual_amount
            )

            account.updated_at = datetime.now(timezone.utc)

            message = "Prihod je uspjesno evidentiran."

        db.commit()
        db.refresh(income)
        db.refresh(account)

        delay_days = (
            income.actual_date - income.expected_date
        ).days

        result = {
            "status": "success",
            "message": message,
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
            detail=(
                "Greska prilikom evidentiranja prihoda: "
                f"{str(error)}"
            )
        )

    finally:
        db.close()

    if request.actual_date <= date.today():
        await run_agent_once()

    return result
