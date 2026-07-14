import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_db
    db = TestingSessionLocal()
    seed_db(db)
    db.close()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "application": "X-DMRA Rescue"}

def test_get_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_incidents" in data
    assert data["total_incidents"] == 3

def test_get_incidents():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_create_valid_incident():
    payload = {
        "title": "Test Incident",
        "description": "Test Desc",
        "incident_type": "Fire",
        "latitude": 34.0,
        "longitude": -118.0,
        "severity": "high",
        "affected_people": 10,
        "injured_people": 2,
        "vulnerable_people": 1
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Incident"
    assert data["status"] == "reported"

def test_create_invalid_incident():
    payload = {
        "title": "", # invalid empty string
        "description": "Test Desc",
        "incident_type": "Fire",
        "latitude": 100.0, # invalid latitude
        "longitude": -118.0,
        "severity": "high",
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 422 # Validation error

def test_get_missing_incident():
    response = client.get("/api/incidents/999")
    assert response.status_code == 404

def test_get_teams():
    response = client.get("/api/teams")
    assert response.status_code == 200
    assert len(response.json()) == 5
