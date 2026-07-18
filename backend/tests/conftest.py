import pytest
import os
import sys

os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_user(db_session, email, role, is_active=True, password="TestPass123"):
    from app.models import User, UserRole
    from app.core.security import hash_password
    user = User(
        full_name=f"User {email}",
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=1 if is_active else 0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _token_for(user, db_session):
    from app.core.security import create_access_token
    token, _ = create_access_token(user.id, user.email, user.role.value)
    return token


@pytest.fixture(scope="function")
def admin_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "admin@test.com", UserRole.admin)


@pytest.fixture(scope="function")
def admin_token(admin_user):
    return _token_for(admin_user, None)


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def command_officer_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "command_officer@test.com", UserRole.command_officer)


@pytest.fixture(scope="function")
def command_officer_token(command_officer_user):
    return _token_for(command_officer_user, None)


@pytest.fixture(scope="function")
def command_officer_headers(command_officer_token):
    return {"Authorization": f"Bearer {command_officer_token}"}


@pytest.fixture(scope="function")
def rescue_officer_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "rescue_officer@test.com", UserRole.rescue_officer)


@pytest.fixture(scope="function")
def rescue_officer_token(rescue_officer_user):
    return _token_for(rescue_officer_user, None)


@pytest.fixture(scope="function")
def rescue_officer_headers(rescue_officer_token):
    return {"Authorization": f"Bearer {rescue_officer_token}"}


@pytest.fixture(scope="function")
def relief_officer_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "relief_officer@test.com", UserRole.relief_officer)


@pytest.fixture(scope="function")
def relief_officer_token(relief_officer_user):
    return _token_for(relief_officer_user, None)


@pytest.fixture(scope="function")
def relief_officer_headers(relief_officer_token):
    return {"Authorization": f"Bearer {relief_officer_token}"}


@pytest.fixture(scope="function")
def shelter_officer_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "shelter_officer@test.com", UserRole.shelter_officer)


@pytest.fixture(scope="function")
def shelter_officer_token(shelter_officer_user):
    return _token_for(shelter_officer_user, None)


@pytest.fixture(scope="function")
def shelter_officer_headers(shelter_officer_token):
    return {"Authorization": f"Bearer {shelter_officer_token}"}


@pytest.fixture(scope="function")
def viewer_user(db_session):
    from app.models import UserRole
    return _create_user(db_session, "viewer@test.com", UserRole.viewer)


@pytest.fixture(scope="function")
def viewer_token(viewer_user):
    return _token_for(viewer_user, None)


@pytest.fixture(scope="function")
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture(scope="function")
def create_user(db_session):
    from app.models import User, UserRole
    from app.core.security import hash_password

    def _create(email, role=UserRole.admin, is_active=True, password="TestPass123"):
        return _create_user(db_session, email, role, is_active, password)
    return _create


@pytest.fixture(scope="function")
def seeded_db(db_session):
    from app.seed import seed_db
    seed_db(db_session)
    return db_session


@pytest.fixture(scope="function")
def seeded_client(seeded_db):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()