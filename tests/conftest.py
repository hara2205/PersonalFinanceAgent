
import pytest

from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from app.database import Base
from app.main import app
import app.main as main_module


@pytest.fixture
def db():
    """
    Kreira privremenu SQLite bazu u memoriji.

    Svaki test dobija vlastitu bazu, tako da
    testiranje ne utice na glavnu bazu projekta.
    """

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False
    )

    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def client(db, monkeypatch):
    """
    Kreira FastAPI testni klijent.

    Koristi privremenu bazu i iskljucuje
    pozadinsko pokretanje agenta tokom testiranja.
    """

    @asynccontextmanager
    async def test_lifespan(application):
        yield

    monkeypatch.setattr(
        main_module.app.router,
        "lifespan_context",
        test_lifespan
    )

    monkeypatch.setattr(
        main_module,
        "SessionLocal",
        lambda: db
    )

    monkeypatch.setattr(
        "app.agent.SessionLocal",
        lambda: db
    )

    with TestClient(app) as test_client:
        yield test_client
