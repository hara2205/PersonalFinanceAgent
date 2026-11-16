
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.agent import FinancialAgentRunner


# Agent se izvrsava jednom dnevno.
AGENT_INTERVAL = 24 * 60 * 60

# Jedna instanca centralnog agenta.
agent = FinancialAgentRunner()

# Sprjecava istovremeno izvrsavanje vise ciklusa.
agent_lock = asyncio.Lock()


async def run_agent_once():
    """
    Pokrece jedan ciklus finansijskog agenta.

    Koristimo poseban thread kako sinhroni rad
    s bazom ne bi blokirao FastAPI event loop.
    """

    async with agent_lock:
        result = await asyncio.to_thread(agent.step)

        return result


async def periodic_agent_runner():
    """
    Automatski izvrsava agenta svakih 24 sata.

    Prva analiza izvrsava se odmah nakon pokretanja
    FastAPI aplikacije.
    """

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

        # Cekamo 24 sata do naredne analize.
        await asyncio.sleep(AGENT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Upravljanje zivotnim ciklusom aplikacije.

    Prilikom pokretanja backend-a pokrecemo
    pozadinski zadatak agenta.
    """

    print("\n====================================")
    print(" POKRETANJE PERSONAL FINANCE BACKEND-a")
    print("====================================")

    background_task = asyncio.create_task(
        periodic_agent_runner()
    )

    yield

    # Zaustavljanje pozadinskog zadatka
    # prilikom gasenja aplikacije.
    background_task.cancel()

    try:
        await background_task
    except asyncio.CancelledError:
        print("\n[BACKGROUND] Agent je zaustavljen.")

    print("[BACKEND] Aplikacija je ugasena.")


# Kreiranje FastAPI aplikacije.
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
    """
    Pocetna ruta API-ja.
    """

    return {
        "application": "Personal Finance Agent",
        "status": "running",
        "message": "Backend aplikacija je aktivna."
    }


@app.get("/health")
def health_check():
    """
    Provjera dostupnosti backend aplikacije.
    """

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/agent/run")
async def run_agent_manually():
    """
    Rucno pokretanje jednog ciklusa agenta.
    """

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
