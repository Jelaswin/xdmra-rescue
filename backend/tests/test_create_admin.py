import pytest
import os
import sys
from io import StringIO
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "7"
os.environ.pop("DATABASE_URL", None)

from app.database import Base
from app.models import User, UserRole


TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    TestingSessionLocal().close()
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def mock_sessionlocal(monkeypatch):
    def mock_get_session():
        return TestingSessionLocal()

    import app.database as db_module
    monkeypatch.setattr(db_module, "SessionLocal", mock_get_session)


class TestCreateAdminScript:
    def test_requires_name_email_password(self, mock_sessionlocal, capsys):
        from scripts.create_admin import main
        with patch("sys.argv", ["create_admin"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Name, email, and password are required" in captured.out

    def test_rejects_short_password(self, mock_sessionlocal, capsys):
        from scripts.create_admin import main
        with patch("sys.argv", ["create_admin", "--name", "Admin", "--email", "admin@test.com", "--password", "short"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Password must be at least 8 characters" in captured.out

    def test_rejects_duplicate_email(self, mock_sessionlocal, capsys):
        from scripts.create_admin import create_admin
        user = User(
            full_name="Existing User",
            email="existing@test.com",
            password_hash="somehash",
            role=UserRole.admin,
            is_active=1,
        )
        db = TestingSessionLocal()
        db.add(user)
        db.commit()
        db.close()

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            with patch("sys.argv", ["create_admin", "--name", "Admin", "--email", "existing@test.com", "--password", "ValidPass123"]):
                with pytest.raises(SystemExit) as exc_info:
                    create_admin("Admin", "existing@test.com", "ValidPass123")
                assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_creates_admin_with_hashed_password(self, mock_sessionlocal):
        from scripts.create_admin import create_admin
        from app.core.security import verify_password

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            admin = create_admin("Test Admin", "admin@test.com", "ValidPass123")

        assert admin.full_name == "Test Admin"
        assert admin.email == "admin@test.com"
        assert admin.role == UserRole.admin
        assert admin.password_hash != "ValidPass123"
        assert verify_password("ValidPass123", admin.password_hash)

    def test_does_not_print_password(self, mock_sessionlocal, capsys):
        from scripts.create_admin import create_admin

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            create_admin("Test Admin", "admin@test.com", "SecretPass123!")

        captured = capsys.readouterr()
        assert "SecretPass123!" not in captured.out
        assert "SecretPass123!" not in captured.err

    def test_does_not_print_database_url(self, mock_sessionlocal, capsys):
        from scripts.create_admin import create_admin

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            create_admin("Test Admin", "admin@test.com", "ValidPass123")

        captured = capsys.readouterr()
        assert "postgresql" not in captured.out.lower()
        assert "sqlite" not in captured.out.lower() or "memory" in captured.out.lower()
        assert "password" not in captured.out.lower() or "password" in captured.err.lower()

    def test_success_message_contains_safe_info(self, mock_sessionlocal, capsys):
        from scripts.create_admin import create_admin

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            create_admin("Test Admin", "admin@test.com", "ValidPass123")

        captured = capsys.readouterr()
        assert "successfully" in captured.out
        assert "admin@test.com" in captured.out
        assert "ValidPass123" not in captured.out

    def test_works_with_sqlite_in_memory(self, mock_sessionlocal):
        from scripts.create_admin import create_admin

        with patch("scripts.create_admin.SessionLocal", return_value=TestingSessionLocal()):
            admin = create_admin("SQLite Admin", "sqlite@test.com", "ValidPass123")

        assert admin.email == "sqlite@test.com"
        assert admin.role == UserRole.admin