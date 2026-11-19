import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
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
from app.income_service import (
    activate_due_incomes,
    record_income_receipt,
    IncomeNotFoundError,
    IncomeAlreadyProcessedError,
    AccountStateMissingError
)


AGENT_INTERVAL = 24 * 60 * 60

agent = FinancialAgentRunner()
agent_lock = asyncio.Lock()


# ==========================================
# PYDANTIC MODELI ZA ZAHTJEVE
# ==========================================

class CreateIncomeRequest(BaseModel):
    source_name: str = Field(min_length=1, max_length=100)
    expected_date: date
    expected_amount: Decimal = Field(gt=0)


class CreateObligationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    amount: Decimal = Field(gt=0)
    due_date: date


class ReceiveIncomeRequest(BaseModel):
    actual_date: date
    actual_amount: Decimal = Field(gt=0)


# ==========================================
# AKTIVIRANJE BUDUCIH UPLATA (PREKO SERVISA)
# ==========================================

def _activate_due_incomes_with_session(reference_date: date) -> int:
    """Otvara sesiju i poziva aplikacijski servis za aktivaciju dospjelih uplata."""
    db = SessionLocal()
    try:
        return activate_due_incomes(db, reference_date=reference_date)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ==========================================
# POKRETANJE AGENTA
# ==========================================

async def run_agent_once(simulation_date: date | None = None):
    reference_date = simulation_date or date.today()

    async with agent_lock:
        activated_count = await asyncio.to_thread(
            _activate_due_incomes_with_session,
            reference_date
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


# ==========================================
# LIFESPAN
# ==========================================

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


# ==========================================
# FASTAPI APLIKACIJA
# ==========================================

app = FastAPI(
    title="Personal Finance Agent API",
    description=(
        "API za pracenje finansijskih obaveza, "
        "predvidjanje prihoda i analizu likvidnosti."
    ),
    version="1.3.1",
    lifespan=lifespan
)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/ui",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)


# ==========================================
# POMOCNA RUTA
# ==========================================

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


# ==========================================
# RUCNO POKRETANJE AGENTA
# ==========================================

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


# ==========================================
# DODAVANJE OCEKIVANOG PRIHODA
# ==========================================

@app.post("/incomes")
async def create_income(request: CreateIncomeRequest):
    db = SessionLocal()

    try:
        income = IncomePayment(
            source_name=request.source_name.strip(),
            expected_date=request.expected_date,
            expected_amount=request.expected_amount,
            status="Expected"
        )

        if not income.source_name:
            raise HTTPException(
                status_code=422,
                detail="Izvor prihoda ne moze biti prazan."
            )

        db.add(income)
        db.commit()
        db.refresh(income)

        result = {
            "status": "success",
            "message": "Ocekivani prihod je uspjesno dodan.",
            "income": {
                "id": income.id,
                "source": income.source_name,
                "expected_date": income.expected_date.isoformat(),
                "expected_amount": float(income.expected_amount),
                "status": income.status
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Greska prilikom dodavanja prihoda: {str(error)}"
        )

    finally:
        db.close()

    await run_agent_once()

    return result


# ==========================================
# DODAVANJE FINANSIJSKE OBAVEZE
# ==========================================

@app.post("/obligations")
async def create_obligation(request: CreateObligationRequest):
    db = SessionLocal()

    try:
        obligation = Obligation(
            title=request.title.strip(),
            amount=request.amount,
            due_date=request.due_date,
            status="Pending"
        )

        if not obligation.title:
            raise HTTPException(
                status_code=422,
                detail="Naziv obaveze ne moze biti prazan."
            )

        db.add(obligation)
        db.commit()
        db.refresh(obligation)

        result = {
            "status": "success",
            "message": "Finansijska obaveza je uspjesno dodana.",
            "obligation": {
                "id": obligation.id,
                "title": obligation.title,
                "amount": float(obligation.amount),
                "due_date": obligation.due_date.isoformat(),
                "status": obligation.status
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Greska prilikom dodavanja obaveze: "
                f"{str(error)}"
            )
        )

    finally:
        db.close()

    await run_agent_once()

    return result


# ==========================================
# FINANSIJSKI PREGLED
# ==========================================

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


# ==========================================
# AKTIVNA UPOZORENJA
# ==========================================

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


# ==========================================
# FINANSIJSKA PROGNOZA
# ==========================================

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


# ==========================================
# EVIDENTIRANJE PRIMLJENOG PRIHODA (DELEGIRA SERVISU)
# ==========================================

@app.post("/incomes/{income_id}/receive")
async def receive_income(
    income_id: int,
    request: ReceiveIncomeRequest
):
    db = SessionLocal()
    reference_date = date.today()

    try:
        service_result = record_income_receipt(
            db=db,
            income_id=income_id,
            actual_date=request.actual_date,
            actual_amount=request.actual_amount,
            reference_date=reference_date
        )

        response_payload = {
            "status": "success",
            "message": service_result["message"],
            "income": service_result["income"],
            "new_account_balance": service_result["new_account_balance"]
        }

    except IncomeNotFoundError as error:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(error))

    except IncomeAlreadyProcessedError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(error))

    except AccountStateMissingError as error:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(error))

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

    if service_result["balance_updated"]:
        await run_agent_once(reference_date)

    return response_payload