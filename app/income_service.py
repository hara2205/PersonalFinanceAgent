# app/income_service.py
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import AccountState, IncomePayment

class IncomeNotFoundError(Exception):
    """Prihod nije pronadjen u bazi."""

class IncomeAlreadyProcessedError(Exception):
    """Prihod je vec evidentiran kao primljen ili zakazan."""

class AccountStateMissingError(Exception):
    """Stanje racuna nije inicijalizovano u bazi."""

def classify_income_status(actual_date: date, reference_date: date) -> str:
    """Odreduje da li je uplata zakazana za buducnost ili odmah realizovana."""
    if actual_date > reference_date:
        return "ScheduledReceived"
    return "Received"

def should_update_balance_on_receipt(status: str) -> bool:
    """Saldo se odmah mijenja samo ako je uplata realizovana ('Received')."""
    return status == "Received"

def record_income_receipt(
    db: Session,
    income_id: int,
    actual_date: date,
    actual_amount: Decimal,
    reference_date: date | None = None
) -> dict:
    """
    Aplikacijski servis koji primjenjuje poslovna pravila evidentiranja prihoda:
    - odlucuje kada je uplata zakazana ili realizovana,
    - odlucuje kada mijenja saldo racuna,
    - perzistira promjene u bazi.
    """
    current_date = reference_date or date.today()

    income = db.query(IncomePayment).filter(IncomePayment.id == income_id).first()
    if income is None:
        raise IncomeNotFoundError("Prihod nije pronadjen.")

    if income.status != "Expected":
        raise IncomeAlreadyProcessedError("Ovaj prihod je vec evidentiran ili zakazan.")

    account = db.query(AccountState).order_by(AccountState.id).first()
    if account is None:
        raise AccountStateMissingError("Finansijsko stanje racuna nije pronadjeno.")

    clean_amount = Decimal(str(actual_amount))
    new_status = classify_income_status(actual_date, current_date)
    balance_updated = should_update_balance_on_receipt(new_status)

    income.actual_date = actual_date
    income.actual_amount = clean_amount
    income.status = new_status

    if balance_updated:
        account.current_balance = Decimal(account.current_balance) + clean_amount
        account.updated_at = datetime.now(timezone.utc)
        message = "Prihod je uspjesno evidentiran."
    else:
        message = "Buduca uplata je evidentirana. Saldo ce biti azuriran na datum uplate."

    db.commit()
    db.refresh(income)
    db.refresh(account)

    delay_days = (income.actual_date - income.expected_date).days

    return {
        "message": message,
        "balance_updated": balance_updated,
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

def activate_due_incomes(db: Session, reference_date: date | None = None) -> int:
    """
    Aktivira sve zakazane uplate cije je dospijece nastupilo 
    zakljucno sa referentnim datumom i azurira saldo racuna.
    """
    current_date = reference_date or date.today()

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

    account = db.query(AccountState).order_by(AccountState.id).first()
    if account is None:
        raise AccountStateMissingError("Finansijsko stanje racuna nije pronadjeno.")

    activated_count = 0
    for income in due_incomes:
        income.status = "Received"
        account.current_balance = Decimal(account.current_balance) + Decimal(income.actual_amount)
        activated_count += 1

    account.updated_at = datetime.now(timezone.utc)
    db.commit()

    return activated_count