"""
Login and token auth through the real router: POST /api/auth/login, then a request with the token.
"""

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mc import config, users
from mc.server import deps
from mc.server import routes_auth
from mc.server.auth_helper import create_jwt_access_token

API_KEY = "auth-test-api-key"


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    users_file = str(tmp_path / "users.json")
    users.create_user_file(users_file)
    users.add_user("operator", "secret-pw", users_file)
    monkeypatch.setattr(
        routes_auth, "authenticate_user", lambda username, password: users.authenticate_user(username, password, users_file)
    )
    monkeypatch.setattr(deps, "MC_API_KEY", API_KEY)

    app = FastAPI()
    app.include_router(routes_auth.router, prefix="/api")
    return TestClient(app)


def login(client: TestClient, password: str = "secret-pw"):
    return client.post("/api/auth/login", data={"username": "operator", "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_then_request_with_token(client):
    res = login(client)
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"

    res = client.get("/api/auth/user", headers=bearer(res.json()["access_token"]))
    assert res.status_code == 200
    assert res.json() == {"username": "operator"}


def test_login_wrong_password(client):
    assert login(client, password="wrong").status_code == 401


def test_request_without_credentials(client):
    assert client.get("/api/auth/user").status_code == 401


def test_token_claims():
    token = create_jwt_access_token({"sub": "operator"})
    claims = pyjwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM], audience=config.JWT_AUDIENCE)
    assert claims["sub"] == "operator"
    assert claims["iss"] == config.JWT_ISSUER
    assert {"exp", "iat", "nbf", "jti"} <= claims.keys()


def _forged_token(**overrides) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": "operator",
        "iss": config.JWT_ISSUER,
        "aud": config.JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "jti": "test",
    }
    key = overrides.pop("key", config.JWT_SECRET_KEY)
    algorithm = overrides.pop("algorithm", config.JWT_ALGORITHM)
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return pyjwt.encode(claims, key, algorithm=algorithm)


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": datetime.now(UTC) - timedelta(minutes=1)},  # expired
        {"key": "some-other-secret-key-with-32-bytes"},  # wrong signature
        {"aud": "other"},  # wrong audience
        {"iss": "other"},  # wrong issuer
        {"sub": None},  # missing subject
        {"algorithm": "HS512"},  # algorithm not allowed
    ],
    ids=["expired", "bad-signature", "wrong-audience", "wrong-issuer", "no-subject", "wrong-algorithm"],
)
def test_invalid_tokens_are_rejected(client, overrides):
    res = client.get("/api/auth/user", headers=bearer(_forged_token(**overrides)))
    assert res.status_code == 401


def test_unsigned_token_is_rejected(client):
    token = pyjwt.encode({"sub": "operator"}, key=None, algorithm="none")
    assert client.get("/api/auth/user", headers=bearer(token)).status_code == 401


def test_api_key(client):
    assert client.get("/api/auth/user", headers={"x-api-key": API_KEY}).json() == {"username": "api-key-user"}
    assert client.get("/api/auth/user", headers={"x-api-key": "wrong-key-123"}).status_code == 401
