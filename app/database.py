
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Glavni folder projekta
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder u kojem će se nalaziti SQLite baza
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

# Lokacija baze podataka
DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'personal_finance.db'}"


# Kreiranje konekcije s bazom
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# Kreiranje sesija za rad s bazom
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Osnovna klasa za sve modele baze
class Base(DeclarativeBase):
    pass


# Funkcija za dobijanje sesije baze
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
