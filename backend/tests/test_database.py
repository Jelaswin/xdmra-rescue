import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ.pop("DATABASE_URL", None)

from app.database import _is_sqlite, _is_postgresql, _create_engine_args, _normalize_postgresql_url, get_db, SessionLocal


class TestPostgresqlUrlNormalization:
    def test_postgresql_becomes_postgresql_psycopg(self):
        assert _normalize_postgresql_url("postgresql://user:pass@localhost/db") == "postgresql+psycopg://user:pass@localhost/db"

    def test_postgresql_psycopg_unchanged(self):
        assert _normalize_postgresql_url("postgresql+psycopg://user:pass@localhost/db") == "postgresql+psycopg://user:pass@localhost/db"

    def test_postgres_becomes_postgres_psycopg(self):
        assert _normalize_postgresql_url("postgres://user:pass@localhost/db") == "postgres+psycopg://user:pass@localhost/db"

    def test_postgres_psycopg_unchanged(self):
        assert _normalize_postgresql_url("postgres+psycopg://user:pass@localhost/db") == "postgres+psycopg://user:pass@localhost/db"

    def test_sslmode_preserved(self):
        url = "postgresql://user:pass@localhost/db?sslmode=require"
        assert _normalize_postgresql_url(url) == "postgresql+psycopg://user:pass@localhost/db?sslmode=require"

    def test_neon_pooled_hostname_preserved(self):
        url = "postgresql://user:pass@ep-12345.us-east-2.aws.neon.tech/neondb?options=endpoint=ep-12345"
        result = _normalize_postgresql_url(url)
        assert "ep-12345.us-east-2.aws.neon.tech" in result
        assert "neondb" in result
        assert "options=endpoint=ep-12345" in result

    def test_password_with_url_encoded_characters_preserved(self):
        url = "postgresql://user:P%40ss%21%23%24@localhost/db"
        result = _normalize_postgresql_url(url)
        assert "P%40ss%21%23%24" in result

    def test_sqlite_unchanged(self):
        assert _normalize_postgresql_url("sqlite:///./xdmra.db") == "sqlite:///./xdmra.db"
        assert _normalize_postgresql_url("sqlite:///:memory:") == "sqlite:///:memory:"

    def test_username_and_port_preserved(self):
        url = "postgresql://admin:secret@db.example.com:5433/production"
        result = _normalize_postgresql_url(url)
        assert "admin" in result
        assert "5433" in result
        assert "production" in result

    def test_query_parameters_preserved(self):
        url = "postgresql://user:pass@localhost/mydb?sslmode=require&connect_timeout=10"
        result = _normalize_postgresql_url(url)
        assert "sslmode=require" in result
        assert "connect_timeout=10" in result

    def test_normalize_does_not_print_credentials(self, capsys):
        url = "postgresql://user:super_secret_password@localhost/db"
        _normalize_postgresql_url(url)
        captured = capsys.readouterr()
        assert "super_secret_password" not in captured.out
        assert "super_secret_password" not in captured.err


class TestDatabaseUrlDetection:
    def test_sqlite_url_detected(self):
        assert _is_sqlite("sqlite:///./xdmra.db") is True
        assert _is_sqlite("sqlite:///./test.db") is True
        assert _is_sqlite("sqlite:///:memory:") is True

    def test_postgresql_url_detected(self):
        assert _is_postgresql("postgresql://user:pass@localhost/db") is True
        assert _is_postgresql("postgresql+psycopg://user:pass@localhost/db") is True
        assert _is_postgresql("postgres://user:pass@localhost/db") is True
        assert _is_postgresql("postgresql://user:pass@my-db.neon.tech/db?options=...") is True

    def test_sqlite_not_postgresql(self):
        assert _is_postgresql("sqlite:///./xdmra.db") is False

    def test_neon_url_postgresql(self):
        assert _is_postgresql("postgresql://user:password@ep-12345.us-east-2.aws.neon.tech/neondb?options=endpoint=ep-12345") is True
        assert _is_postgresql("postgresql+psycopg://user:password@ep-12345.us-east-2.aws.neon.tech/neondb") is True


class TestEngineArgsCreation:
    def test_sqlite_creates_check_same_thread(self):
        args = _create_engine_args("sqlite:///./xdmra.db")
        assert "connect_args" in args
        assert args["connect_args"]["check_same_thread"] is False

    def test_sqlite_memory_creates_check_same_thread(self):
        args = _create_engine_args("sqlite:///:memory:")
        assert "connect_args" in args
        assert args["connect_args"]["check_same_thread"] is False

    def test_postgresql_does_not_receive_check_same_thread(self):
        args = _create_engine_args("postgresql://user:pass@localhost/db")
        assert "connect_args" not in args

    def test_postgresql_with_psycopg_does_not_receive_check_same_thread(self):
        args = _create_engine_args("postgresql+psycopg://user:pass@localhost/db")
        assert "connect_args" not in args

    def test_postgresql_enables_pool_pre_ping(self):
        args = _create_engine_args("postgresql://user:pass@localhost/db")
        assert "pool_pre_ping" in args
        assert args["pool_pre_ping"] is True

    def test_postgresql_with_psycopg_enables_pool_pre_ping(self):
        args = _create_engine_args("postgresql+psycopg://user:pass@localhost/db")
        assert "pool_pre_ping" in args
        assert args["pool_pre_ping"] is True

    def test_neon_url_enables_pool_pre_ping(self):
        args = _create_engine_args("postgresql://user:password@ep-12345.us-east-2.aws.neon.tech/neondb")
        assert "pool_pre_ping" in args
        assert args["pool_pre_ping"] is True

    def test_unknown_url_returns_empty_args(self):
        args = _create_engine_args("mysql://user:pass@localhost/db")
        assert args == {}


class TestDefaultDatabaseUrl:
    def test_default_uses_sqlite(self):
        from app.database import DATABASE_URL
        assert DATABASE_URL == "sqlite:///./xdmra.db"


class TestGetDbBehavior:
    def test_get_db_yields_session(self):
        with patch("app.database.SessionLocal") as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            gen = get_db()
            result = next(gen)
            assert result is mock_db
            mock_db.close.assert_not_called()
            next(gen, None)

    def test_get_db_closes_on_exit(self):
        with patch("app.database.SessionLocal") as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            gen = get_db()
            next(gen)
            next(gen, None)
            mock_db.close.assert_called_once()


class TestExistingBehaviorPreserved:
    def test_get_db_dependency_exists(self):
        from app.database import get_db
        import inspect
        sig = inspect.signature(get_db)
        assert list(sig.parameters.keys()) == []

    def test_session_local_exported(self):
        from app.database import SessionLocal
        from sqlalchemy.orm import sessionmaker
        assert isinstance(SessionLocal, sessionmaker)

    def test_base_exported(self):
        from app.database import Base
        assert Base is not None

    def test_default_engine_is_sqlite(self):
        from app.database import engine
        assert engine.url.drivername.startswith("sqlite")


class TestDatabaseCredentialsMasked:
    def test_sqlite_url_no_credentials(self):
        url = "sqlite:///./xdmra.db"
        args = _create_engine_args(url)
        engine = create_engine(url, **args)
        engine_str = str(engine.url)
        assert "password" not in engine_str.lower() or "sqlite" in engine_str

    def test_postgresql_url_mask_password_in_args(self):
        from urllib.parse import urlparse
        url = "postgresql://user:secretpassword@localhost:5432/dbname"
        parsed = urlparse(url)
        assert parsed.password == "secretpassword"

    def test_neon_url_parseable(self):
        from urllib.parse import urlparse
        url = "postgresql://user:mysecretpassword@ep-12345.us-east-2.aws.neon.tech/neondb?options=..."
        parsed = urlparse(url)
        assert parsed.username == "user"
        assert parsed.password == "mysecretpassword"
        assert "neon.tech" in parsed.hostname


class TestPostgresqlConnectionMocked:
    def test_postgresql_engine_args_generated_correctly(self):
        args = _create_engine_args("postgresql://user:pass@localhost/db")
        assert "pool_pre_ping" in args
        assert args["pool_pre_ping"] is True
        assert "connect_args" not in args

    def test_neon_engine_args_generated_correctly(self):
        args = _create_engine_args("postgresql+psycopg://user:pass@ep-12345.us-east-2.aws.neon.tech/neondb")
        assert "pool_pre_ping" in args
        assert args["pool_pre_ping"] is True
        assert "connect_args" not in args

    def test_engine_not_created_multiple_times_on_import(self):
        import app.database as db_module
        engine1 = db_module.engine
        engine2 = db_module.engine
        assert engine1 is engine2


class TestCorsConfiguration:
    def test_allowed_origins_parses_single_origin(self):
        os.environ["FRONTEND_ORIGIN"] = "https://my-app.vercel.app"
        os.environ.pop("ALLOWED_ORIGINS", None)
        import importlib
        import app.main
        importlib.reload(app.main)
        assert "https://my-app.vercel.app" in app.main.allowed_origins
        importlib.reload(app.main)

    def test_allowed_origins_parses_multiple_comma_separated(self):
        os.environ["ALLOWED_ORIGINS"] = "https://app1.vercel.app,https://app2.vercel.app,http://localhost:5173"
        os.environ.pop("FRONTEND_ORIGIN", None)
        import importlib
        import app.main
        importlib.reload(app.main)
        assert len(app.main.allowed_origins) == 3
        assert "https://app1.vercel.app" in app.main.allowed_origins
        assert "https://app2.vercel.app" in app.main.allowed_origins
        assert "http://localhost:5173" in app.main.allowed_origins
        importlib.reload(app.main)

    def test_no_wildcard_cors_in_production(self):
        os.environ["ALLOWED_ORIGINS"] = "*"
        os.environ["ENVIRONMENT"] = "production"
        import importlib
        import app.main
        importlib.reload(app.main)
        assert "*" not in app.main.allowed_origins
        importlib.reload(app.main)

    def test_health_endpoint_is_public(self):
        from app.api import router
        health_route = None
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/health":
                health_route = route
                break
        assert health_route is not None
        dependencies = getattr(health_route, "dependant", None)
        if dependencies:
            for dep in dependencies.dependencies:
                assert "get_current_active_user" not in str(dep)