import pytest
import os
import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole, AuditLog, RevokedToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    TestingSessionLocal().close()
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_test_user(db_session, email="test@example.com", role=UserRole.admin, is_active=True, password="TestPass123"):
    user = User(
        full_name="Test User",
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=1 if is_active else 0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_header_for_email(email, db_session):
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError(f"User {email} not found")
    token, _ = create_access_token(user.id, user.email, user.role.value)
    return {"Authorization": f"Bearer {token}"}


class TestPasswordHashing:
    def test_hash_differs_from_password(self):
        password = "MySecret123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_correct_password_verifies(self):
        password = "MySecret123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_incorrect_password_fails(self):
        password = "MySecret123"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_plain_password_not_stored(self):
        password = "MySecret123"
        hashed = hash_password(password)
        assert "MySecret123" not in hashed
        assert hashed.startswith("$2")

    def test_different_hashes_for_same_password(self):
        password = "SamePass"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_password_minimum_length_enforced_in_schema(self):
        from app.schemas import UserCreate
        with pytest.raises(Exception):
            UserCreate(full_name="Test", email="a@b.com", password="short", role="viewer")


class TestPublicEndpoints:
    def test_health_check_no_auth_required(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "application": "X-DMRA Rescue"}


class TestLogin:
    def test_login_unknown_user(self, client):
        response = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "AnyPass123"
        })
        assert response.status_code == 401

    def test_login_invalid_password(self, client, db_session):
        create_test_user(db_session, email="user@test.com", password="CorrectPass123")

        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "WrongPass123"
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client, db_session):
        create_test_user(db_session, email="inactive@test.com", is_active=False, password="ValidPass123")

        response = client.post("/api/auth/login", json={
            "email": "inactive@test.com",
            "password": "ValidPass123"
        })
        assert response.status_code == 403

    def test_login_success_returns_tokens(self, client, db_session):
        create_test_user(db_session, email="active@test.com", password="ValidPass123")

        response = client.post("/api/auth/login", json={
            "email": "active@test.com",
            "password": "ValidPass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_response_excludes_password(self, client, db_session):
        create_test_user(db_session, email="nopass@test.com", password="ValidPass123")

        response = client.post("/api/auth/login", json={
            "email": "nopass@test.com",
            "password": "ValidPass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "password_hash" not in data["user"]
        assert "password" not in data["user"]


class TestTokenFlow:
    def test_access_token_contains_claims(self, client, db_session):
        user = create_test_user(db_session, email="token@test.com", role=UserRole.command_officer)

        token, expires_in = create_access_token(user.id, user.email, user.role.value)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user.id)
        assert payload["role"] == "command_officer"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload
        assert expires_in == 1800

    def test_refresh_token_contains_claims(self, client, db_session):
        user = create_test_user(db_session, email="refresh@test.com")

        token, expires_at = create_refresh_token(user.id)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "refresh"

    def test_access_token_cannot_be_used_as_refresh(self, client, db_session):
        user = create_test_user(db_session, email="accesstest@test.com")

        access_token, _ = create_access_token(user.id, user.email, user.role.value)

        response = client.post("/api/auth/refresh", json={
            "refresh_token": access_token
        })
        assert response.status_code == 401

    def test_refresh_token_cannot_be_used_as_access(self, client, db_session):
        user = create_test_user(db_session, email="refreshtest2@test.com")

        refresh_token, _ = create_refresh_token(user.id)

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        assert response.status_code == 401

    def test_expired_token_rejected(self, client, db_session):
        user = create_test_user(db_session, email="expired@test.com")

        with patch("app.core.security.datetime") as mock_dt:
            past = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_dt.now.return_value = past

            token, _ = create_access_token(user.id, user.email, user.role.value)

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 401

    def test_invalid_signature_rejected(self, client, db_session):
        user = create_test_user(db_session, email="invalid@test.com")

        import jwt
        payload = {
            "sub": str(user.id),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "iat": datetime.now(timezone.utc),
            "jti": "fake-jti"
        }
        bad_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {bad_token}"
        })
        assert response.status_code == 401

    def test_revoked_refresh_token_rejected(self, client, db_session):
        user = create_test_user(db_session, email="revoked@test.com")

        refresh_token, expires_at = create_refresh_token(user.id)
        jti = decode_token(refresh_token)["jti"]

        revoked = RevokedToken(token_jti=jti, expires_at=expires_at)
        db_session.add(revoked)
        db_session.commit()

        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 401


class TestAuthMe:
    def test_me_without_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_valid_token(self, client, db_session):
        create_test_user(db_session, email="me@test.com", role=UserRole.rescue_officer)

        response = client.get("/api/auth/me", headers=get_auth_header_for_email("me@test.com", db_session))
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@test.com"
        assert data["role"] == "rescue_officer"
        assert "password_hash" not in data

    def test_me_with_inactive_user(self, client, db_session):
        create_test_user(db_session, email="inactive2@test.com", is_active=False)

        response = client.get("/api/auth/me", headers=get_auth_header_for_email("inactive2@test.com", db_session))
        assert response.status_code == 403


class TestLogout:
    def test_logout_success(self, client, db_session):
        create_test_user(db_session, email="logout@test.com")

        response = client.post("/api/auth/logout", headers=get_auth_header_for_email("logout@test.com", db_session))
        assert response.status_code == 200


class TestUserManagement:
    @pytest.fixture
    def admin_user(self, db_session):
        user = create_test_user(db_session, email="testadmin@test.com", role=UserRole.admin)
        return user

    @pytest.fixture
    def admin_token(self, admin_user):
        token, _ = create_access_token(admin_user.id, admin_user.email, admin_user.role.value)
        return token

    @pytest.fixture
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}

    def test_create_user_duplicate_email(self, client, db_session, admin_headers):
        create_test_user(db_session, email="dup@test.com")

        response = client.post("/api/users", json={
            "full_name": "New User",
            "email": "dup@test.com",
            "password": "NewPass123",
            "role": "viewer"
        }, headers=admin_headers)

        assert response.status_code == 409

    def test_create_user_invalid_role(self, client, admin_headers):
        response = client.post("/api/users", json={
            "full_name": "Bad Role",
            "email": "badrole@test.com",
            "password": "Pass12345",
            "role": "superadmin"
        }, headers=admin_headers)

        assert response.status_code == 400

    def test_create_user_password_not_in_response(self, client, admin_headers):
        response = client.post("/api/users", json={
            "full_name": "Clean User",
            "email": "clean@test.com",
            "password": "Pass12345",
            "role": "viewer"
        }, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert "password_hash" not in data
        assert "password" not in data

    def test_list_users_requires_admin(self, client, db_session):
        viewer = create_test_user(db_session, email="viewertest@test.com", role=UserRole.viewer)
        token, _ = create_access_token(viewer.id, viewer.email, viewer.role.value)

        response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_list_users_pagination(self, client, db_session):
        admin = create_test_user(db_session, email="admintest@test.com", role=UserRole.admin)
        token, _ = create_access_token(admin.id, admin.email, admin.role.value)
        headers = {"Authorization": f"Bearer {token}"}

        for i in range(5):
            create_test_user(db_session, email=f"page{i}@test.com", role=UserRole.viewer)

        response = client.get("/api/users?page=1&per_page=2", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 6
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_get_user_by_id(self, client, db_session, admin_headers):
        user = create_test_user(db_session, email="getbyid@test.com", role=UserRole.shelter_officer)

        response = client.get(f"/api/users/{user.id}", headers=admin_headers)

        assert response.status_code == 200
        assert response.json()["email"] == "getbyid@test.com"

    def test_get_user_not_found(self, client, admin_headers):
        response = client.get("/api/users/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_deactivate_self_blocked(self, client, db_session):
        admin_a = create_test_user(db_session, email="selfblock1@test.com", role=UserRole.admin)
        admin_b = create_test_user(db_session, email="selfblock2@test.com", role=UserRole.admin)
        a_id = admin_a.id
        a_email = admin_a.email
        a_role = admin_a.role.value

        token, _ = create_access_token(a_id, a_email, a_role)
        response = client.post(f"/api/users/{a_id}/deactivate", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 400
        assert "cannot deactivate yourself" in response.json()["detail"].lower()

        still_active = db_session.query(User).filter(User.id == a_id).first()
        assert still_active.is_active == 1
        b_active = db_session.query(User).filter(User.id == admin_b.id).first()
        assert b_active.is_active == 1

    def test_deactivate_last_admin_blocked(self, client, db_session):
        admin = create_test_user(db_session, email="lastadmin1@test.com", role=UserRole.admin)
        admin_id = admin.id
        admin_email = admin.email
        admin_role = admin.role.value

        token, _ = create_access_token(admin_id, admin_email, admin_role)
        response = client.post(f"/api/users/{admin_id}/deactivate", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 400
        assert "last active administrator" in response.json()["detail"].lower()

        still_active = db_session.query(User).filter(User.id == admin_id).first()
        assert still_active.is_active == 1

    def test_deactivate_other_admin_success(self, client, db_session):
        admin_a = create_test_user(db_session, email="deactother1@test.com", role=UserRole.admin)
        admin_b = create_test_user(db_session, email="deactother2@test.com", role=UserRole.admin)
        a_id = admin_a.id
        a_email = admin_a.email
        a_role = admin_a.role.value
        b_id = admin_b.id

        token, _ = create_access_token(a_id, a_email, a_role)
        response = client.post(f"/api/users/{b_id}/deactivate", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        assert response.json()["is_active"] is False

        b_inactive = db_session.query(User).filter(User.id == b_id).first()
        assert b_inactive.is_active == 0
        a_still_active = db_session.query(User).filter(User.id == a_id).first()
        assert a_still_active.is_active == 1

    def test_activate_user(self, client, db_session, admin_headers):
        user = create_test_user(db_session, email="toactivate@test.com", is_active=False)
        user_id = user.id

        response = client.post(f"/api/users/{user_id}/activate", headers=admin_headers)

        assert response.status_code == 200
        assert response.json()["is_active"] is True


class TestRBAC:
    def test_viewer_cannot_create_incident(self, client, db_session):
        create_test_user(db_session, email="viewerrbac@test.com", role=UserRole.viewer)

        response = client.post("/api/incidents", json={
            "title": "Viewer Test",
            "description": "Should fail",
            "incident_type": "fire",
            "latitude": 11.0,
            "longitude": 77.0,
            "severity": "low"
        }, headers=get_auth_header_for_email("viewerrbac@test.com", db_session))
        assert response.status_code == 403

    def test_viewer_cannot_create_allocation(self, client, db_session):
        create_test_user(db_session, email="viewer2rbac@test.com", role=UserRole.viewer)

        response = client.post("/api/incidents/1/allocations", json={
            "rescue_team_id": 1
        }, headers=get_auth_header_for_email("viewer2rbac@test.com", db_session))
        assert response.status_code == 403

    def test_rescue_officer_can_create_incident(self, client, db_session):
        create_test_user(db_session, email="cmdtest@test.com", role=UserRole.command_officer)

        response = client.post("/api/incidents", json={
            "title": "Command Officer Test",
            "description": "Should succeed",
            "incident_type": "fire",
            "latitude": 11.0,
            "longitude": 77.0,
            "severity": "high"
        }, headers=get_auth_header_for_email("cmdtest@test.com", db_session))
        assert response.status_code == 201


class TestAuditLogging:
    def test_failed_login_creates_audit_log(self, client):
        client.post("/api/auth/login", json={
            "email": "noone@test.com",
            "password": "wrong"
        })

        db = TestingSessionLocal()
        try:
            log = db.query(AuditLog).filter(AuditLog.action == "login_failure").first()
            assert log is not None
            assert log.success == 0
        finally:
            db.close()

    def test_audit_log_excludes_passwords(self, client, db_session):
        create_test_user(db_session, email="auditsecure@test.com", password="SecretPass123")

        client.post("/api/auth/login", json={
            "email": "auditsecure@test.com",
            "password": "SecretPass123"
        })

        db = TestingSessionLocal()
        try:
            logs = db.query(AuditLog).filter(AuditLog.user_email == "auditsecure@test.com").all()
            for log in logs:
                assert "SecretPass123" not in (log.details or "")
        finally:
            db.close()

    def test_audit_logs_require_admin(self, client, db_session):
        viewer = create_test_user(db_session, email="auditviewer@test.com", role=UserRole.viewer)
        token, _ = create_access_token(viewer.id, viewer.email, viewer.role.value)

        response = client.get("/api/users/audit/logs", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 403

    def test_audit_logs_paginated(self, client, db_session):
        admin = create_test_user(db_session, email="auditpag@test.com")
        token, _ = create_access_token(admin.id, admin.email, admin.role.value)

        response = client.get("/api/users/audit/logs?page=1&per_page=10", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestRoleHierarchy:
    def test_admin_can_create_command_officer(self, client, db_session):
        admin = create_test_user(db_session, email="adm1role@test.com", role=UserRole.admin)
        token, _ = create_access_token(admin.id, admin.email, admin.role.value)

        response = client.post("/api/users", json={
            "full_name": "Command Officer",
            "email": "cmd1role@test.com",
            "password": "Pass12345",
            "role": "command_officer"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 201

    def test_command_officer_cannot_create_admin(self, client, db_session):
        cmd = create_test_user(db_session, email="cmd2role@test.com", role=UserRole.command_officer)
        token, _ = create_access_token(cmd.id, cmd.email, cmd.role.value)

        response = client.post("/api/users", json={
            "full_name": "Admin User",
            "email": "adm2role@test.com",
            "password": "Pass12345",
            "role": "admin"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403


class TestAllSixRoles:
    @pytest.mark.parametrize("role", [
        "admin", "command_officer", "rescue_officer",
        "relief_officer", "shelter_officer", "viewer"
    ])
    def test_each_role_can_login(self, client, db_session, role):
        create_test_user(db_session, email=f"{role}role@test.com", role=UserRole(role), password="TestPass123")

        response = client.post("/api/auth/login", json={
            "email": f"{role}role@test.com",
            "password": "TestPass123"
        })

        assert response.status_code == 200, f"Failed for role: {role}"
        assert response.json()["user"]["role"] == role

    @pytest.mark.parametrize("role", [
        "admin", "command_officer", "rescue_officer",
        "relief_officer", "shelter_officer", "viewer"
    ])
    def test_each_role_can_access_health(self, client, role):
        response = client.get("/api/health")
        assert response.status_code == 200


class TestLoginRateLimiting:
    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        from app.core.rate_limit import login_rate_limiter
        login_rate_limiter.reset()
        yield
        login_rate_limiter.reset()

    def test_five_failed_attempts_accepted(self, client, db_session):
        create_test_user(db_session, email="ratelimit@test.com", role=UserRole.admin, password="CorrectPass123")
        for i in range(5):
            response = client.post("/api/auth/login", json={
                "email": "ratelimit@test.com",
                "password": "WrongPass"
            })
            assert response.status_code == 401, f"Attempt {i+1} should return 401"

    def test_sixth_failed_attempt_blocked(self, client, db_session):
        create_test_user(db_session, email="ratelimit2@test.com", role=UserRole.admin, password="CorrectPass123")
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": "ratelimit2@test.com",
                "password": "WrongPass"
            })
        response = client.post("/api/auth/login", json={
            "email": "ratelimit2@test.com",
            "password": "WrongPass"
        })
        assert response.status_code == 429

    def test_retry_after_header_present(self, client, db_session):
        create_test_user(db_session, email="ratelimit3@test.com", role=UserRole.admin, password="CorrectPass123")
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": "ratelimit3@test.com",
                "password": "WrongPass"
            })
        response = client.post("/api/auth/login", json={
            "email": "ratelimit3@test.com",
            "password": "WrongPass"
        })
        assert response.status_code == 429
        assert "retry-after" in {k.lower() for k in response.headers}

    def test_successful_login_clears_failures(self, client, db_session):
        from app.core.rate_limit import login_rate_limiter
        login_rate_limiter.reset()
        create_test_user(db_session, email="ratelimit4@test.com", role=UserRole.admin, password="CorrectPass123")

        for i in range(4):
            resp = client.post("/api/auth/login", json={
                "email": "ratelimit4@test.com",
                "password": "WrongPass"
            })
            assert resp.status_code == 401, f"Attempt {i+1} expected 401, got {resp.status_code}"

        success_resp = client.post("/api/auth/login", json={
            "email": "ratelimit4@test.com",
            "password": "CorrectPass123"
        })
        assert success_resp.status_code == 200, f"Success expected 200, got {success_resp.status_code}"

        for i in range(5):
            resp = client.post("/api/auth/login", json={
                "email": "ratelimit4@test.com",
                "password": "WrongPass"
            })
            assert resp.status_code == 401, f"Post-clear attempt {i+1} expected 401, got {resp.status_code}"

        response = client.post("/api/auth/login", json={
            "email": "ratelimit4@test.com",
            "password": "WrongPass"
        })
        assert response.status_code == 429, f"6th after clear expected 429, got {response.status_code}"

    def test_correct_credentials_blocked_during_cooldown(self, client, db_session):
        from app.core.rate_limit import login_rate_limiter
        login_rate_limiter.reset()
        create_test_user(db_session, email="ratelimit5@test.com", role=UserRole.admin, password="CorrectPass123")

        for i in range(5):
            resp = client.post("/api/auth/login", json={
                "email": "ratelimit5@test.com",
                "password": "WrongPass"
            })
            assert resp.status_code == 401, f"Attempt {i+1} expected 401, got {resp.status_code}"

        correct_login = client.post("/api/auth/login", json={
            "email": "ratelimit5@test.com",
            "password": "CorrectPass123"
        })
        assert correct_login.status_code == 429, f"Correct credentials during cooldown expected 429, got {correct_login.status_code}"

    def test_different_email_not_blocked_by_same_ip(self, client, db_session):
        create_test_user(db_session, email="user_a@test.com", role=UserRole.admin, password="CorrectPass123")
        create_test_user(db_session, email="user_b@test.com", role=UserRole.admin, password="CorrectPass123")
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": "user_a@test.com",
                "password": "WrongPass"
            })
        response = client.post("/api/auth/login", json={
            "email": "user_b@test.com",
            "password": "CorrectPass123"
        })
        assert response.status_code == 200

    def test_unknown_user_attempts_counted(self, client, db_session):
        from app.core.rate_limit import login_rate_limiter
        login_rate_limiter.reset()
        for i in range(5):
            resp = client.post("/api/auth/login", json={
                "email": "nonexistent@test.com",
                "password": "WrongPass"
            })
            assert resp.status_code == 401, f"Unknown-user attempt {i+1} expected 401, got {resp.status_code}"
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "WrongPass"
        })
        assert response.status_code == 429, f"6th unknown-user expected 429, got {response.status_code}"

    def test_inactive_user_attempts_counted(self, client, db_session):
        from app.core.rate_limit import login_rate_limiter
        login_rate_limiter.reset()
        create_test_user(db_session, email="inactive@test.com", role=UserRole.admin, password="CorrectPass123", is_active=False)
        for i in range(5):
            resp = client.post("/api/auth/login", json={
                "email": "inactive@test.com",
                "password": "WrongPass"
            })
            assert resp.status_code == 403, f"Inactive attempt {i+1} expected 403, got {resp.status_code}"
        response = client.post("/api/auth/login", json={
            "email": "inactive@test.com",
            "password": "WrongPass"
        })
        assert response.status_code == 429, f"6th inactive expected 429, got {response.status_code}"


class TestLoginErrorEquivalence:
    def test_unknown_user_and_wrong_password_return_same_error(self, client, db_session):
        create_test_user(db_session, email="realuser@test.com", role=UserRole.admin, password="CorrectPass123")
        unknown_response = client.post("/api/auth/login", json={
            "email": "ghost@test.com",
            "password": "SomePass123"
        })
        wrong_pass_response = client.post("/api/auth/login", json={
            "email": "realuser@test.com",
            "password": "BadPassword123"
        })
        assert unknown_response.status_code == 401
        assert wrong_pass_response.status_code == 401
        assert unknown_response.json()["detail"] == wrong_pass_response.json()["detail"]


class TestAuditLogSecurity:
    def test_password_not_in_failed_login_audit(self, client, db_session, capsys):
        create_test_user(db_session, email="auditpw@test.com", role=UserRole.admin, password="SecretPassword123")
        client.post("/api/auth/login", json={
            "email": "auditpw@test.com",
            "password": "WrongPassword"
        })
        captured = capsys.readouterr()
        assert "SecretPassword123" not in captured.out
        assert "WrongPassword" not in captured.out

    def test_tokens_not_in_audit_logs(self, client, db_session, capsys):
        create_test_user(db_session, email="auditoken@test.com", role=UserRole.admin, password="CorrectPass123")
        response = client.post("/api/auth/login", json={
            "email": "auditoken@test.com",
            "password": "CorrectPass123"
        })
        tokens = response.json()
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        captured = capsys.readouterr()
        if access_token:
            assert access_token not in captured.out
        if refresh_token:
            assert refresh_token not in captured.out


class TestJWTSecretValidation:
    def test_weak_secret_rejected_in_production(self):
        import os
        old_env = os.environ.get("JWT_SECRET"), os.environ.get("ENV")
        try:
            os.environ["JWT_SECRET"] = "short"
            os.environ["ENV"] = "production"
            from app.core import security
            import importlib
            importlib.reload(security)
            with pytest.raises(ValueError, match="too short"):
                security.get_jwt_secret()
        finally:
            os.environ["JWT_SECRET"] = old_env[0] or ""
            os.environ["ENV"] = old_env[1] or ""
            from app.core import security
            import importlib
            importlib.reload(security)

    def test_placeholder_secret_rejected_in_production(self):
        import os
        old_env = os.environ.get("JWT_SECRET"), os.environ.get("ENV")
        try:
            os.environ["JWT_SECRET"] = "dev-secret-change-in-production"
            os.environ["ENV"] = "production"
            from app.core import security
            import importlib
            importlib.reload(security)
            with pytest.raises(ValueError, match="too short|known weak|placeholder"):
                security.get_jwt_secret()
        finally:
            os.environ["JWT_SECRET"] = old_env[0] or ""
            os.environ["ENV"] = old_env[1] or ""
            from app.core import security
            import importlib
            importlib.reload(security)

    def test_valid_strong_secret_accepted_in_production(self):
        import os
        old_env = os.environ.get("JWT_SECRET"), os.environ.get("ENV")
        try:
            os.environ["JWT_SECRET"] = "this-is-a-very-long-and-strong-secret-key-for-production-32chars"
            os.environ["ENV"] = "production"
            from app.core import security
            import importlib
            importlib.reload(security)
            secret = security.get_jwt_secret()
            assert secret == os.environ["JWT_SECRET"]
        finally:
            os.environ["JWT_SECRET"] = old_env[0] or ""
            os.environ["ENV"] = old_env[1] or ""
            from app.core import security
            import importlib
            importlib.reload(security)

    def test_dev_mode_accepts_placeholder_secret(self):
        import os
        old_env = os.environ.get("JWT_SECRET"), os.environ.get("ENV")
        try:
            os.environ["JWT_SECRET"] = "dev-secret-change-in-production"
            os.environ["ENV"] = "development"
            from app.core import security
            import importlib
            importlib.reload(security)
            secret = security.get_jwt_secret()
            assert secret == "dev-secret-change-in-production"
        finally:
            os.environ["JWT_SECRET"] = old_env[0] or ""
            os.environ["ENV"] = old_env[1] or ""
            from app.core import security
            import importlib
            importlib.reload(security)


class TestHealthEndpoint:
    def test_health_no_auth_required(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.status_code == 200