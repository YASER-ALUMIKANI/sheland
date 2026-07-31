"""
CityLand Backend - Pytest Shared Test Fixtures
# ponytail: Shared in-memory SQLite database using StaticPool & shared cache
"""
import pytest
import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db

# Create a single persistent in-memory SQLite connection with shared cache
test_db_conn = sqlite3.connect("file:memdb1?mode=memory&cache=shared", uri=True, check_same_thread=False)

engine = create_engine(
    "sqlite://",
    creator=lambda: test_db_conn,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from backend.main import _seed_database_internal
    db = TestingSessionLocal()
    _seed_database_internal(db)
    db.close()
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def client():
    return TestClient(app)
