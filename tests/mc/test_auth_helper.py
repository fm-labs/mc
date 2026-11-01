"""
Unit tests for mc.server.auth_helper: creating and verifying JWT access tokens.
"""

import hashlib
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from mc.server import auth_helper
from mc.server.auth_helper import create_jwt_access_token, verify_jwt_access_token

KEY = auth_helper.JWT_SECRET_KEY


def _claims(**overrides) -> dict:
    """Valid claims for a hand-made token; a value of None removes the claim."""
    now = datetime.now(UTC)
    claims = {
        "sub": "operator",
        "iss": auth_helper.JWT_ISSUER,
        "aud": auth_helper.JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "jti": "test-jti",
    }
    claims.update(overrides)
    return {k: v for k, v in claims.items() if v is not None}


def _encode(claims: dict, key: str = KEY, algorithm: str = "HS256") -> str:
    return pyjwt.encode(claims, key, algorithm=algorithm)


def _assert_rejected(token: str, cause: type[Exception]) -> None:
    with pytest.raises(ValueError, match="Invalid token") as exc_info:
        verify_jwt_access_token(token)
    assert isinstance(exc_info.value.__cause__, cause)


# --- create_jwt_access_token ---------------------------------------------------------------------------------------


def test_create_sets_standard_claims():
    before = datetime.now(UTC).replace(microsecond=0)
    token = create_jwt_access_token({"sub": "operator"})
    claims = pyjwt.decode(token, KEY, algorithms=["HS256"], audience=auth_helper.JWT_AUDIENCE)

    assert claims["sub"] == "operator"
    assert claims["iss"] == auth_helper.JWT_ISSUER
    assert claims["aud"] == auth_helper.JWT_AUDIENCE
    assert claims["iat"] >= before.timestamp()
    assert claims["nbf"] == claims["iat"]
    assert claims["exp"] - claims["iat"] == auth_helper.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_create_keeps_extra_data():
    token = create_jwt_access_token({"sub": "operator", "role": "admin"})
    assert verify_jwt_access_token(token)["role"] == "admin"


def test_create_does_not_change_the_input():
    data = {"sub": "operator"}
    create_jwt_access_token(data)
    assert data == {"sub": "operator"}


def test_create_standard_claims_win_over_input():
    # callers can't extend the expiry or change issuer/audience through the data dict
    far_future = datetime.now(UTC) + timedelta(days=365)
    token = create_jwt_access_token({"sub": "operator", "iss": "evil", "aud": "evil", "exp": far_future})
    claims = verify_jwt_access_token(token)
    assert claims["iss"] == auth_helper.JWT_ISSUER
    assert claims["aud"] == auth_helper.JWT_AUDIENCE
    assert claims["exp"] < far_future.timestamp()


def test_create_unique_jti():
    first = verify_jwt_access_token(create_jwt_access_token({"sub": "operator"}))
    second = verify_jwt_access_token(create_jwt_access_token({"sub": "operator"}))
    assert first["jti"] != second["jti"]


def test_create_header_has_algorithm_and_kid():
    header = pyjwt.get_unverified_header(create_jwt_access_token({"sub": "operator"}))
    assert header["alg"] == "HS256"
    assert header["kid"] == hashlib.md5(KEY.encode()).hexdigest()[:16]


def test_create_kid_changes_with_the_key(monkeypatch):
    kid_before = pyjwt.get_unverified_header(create_jwt_access_token({"sub": "operator"}))["kid"]
    monkeypatch.setattr(auth_helper, "JWT_SECRET_KEY", "another-secret-key-" + "y" * 64)
    kid_after = pyjwt.get_unverified_header(create_jwt_access_token({"sub": "operator"}))["kid"]
    assert kid_before != kid_after
    assert len(kid_after) == 16


# --- verify_jwt_access_token ---------------------------------------------------------------------------------------


def test_verify_roundtrip():
    claims = verify_jwt_access_token(create_jwt_access_token({"sub": "operator"}))
    assert claims["sub"] == "operator"


def test_verify_accepts_hand_made_valid_token():
    assert verify_jwt_access_token(_encode(_claims()))["sub"] == "operator"


def test_verify_rejects_token_without_subject():
    # create_jwt_access_token doesn't require a subject, but verify does
    _assert_rejected(create_jwt_access_token({}), pyjwt.MissingRequiredClaimError)


@pytest.mark.parametrize("claim", ["sub", "iss", "aud", "exp", "iat", "nbf", "jti"])
def test_verify_requires_claim(claim):
    _assert_rejected(_encode(_claims(**{claim: None})), pyjwt.MissingRequiredClaimError)


def test_verify_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(auth_helper, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    _assert_rejected(create_jwt_access_token({"sub": "operator"}), pyjwt.ExpiredSignatureError)


def test_verify_rejects_token_not_yet_valid():
    _assert_rejected(_encode(_claims(nbf=datetime.now(UTC) + timedelta(minutes=5))), pyjwt.ImmatureSignatureError)


def test_verify_rejects_wrong_issuer():
    _assert_rejected(_encode(_claims(iss="someone-else")), pyjwt.InvalidIssuerError)


def test_verify_rejects_wrong_audience():
    _assert_rejected(_encode(_claims(aud="someone-else")), pyjwt.InvalidAudienceError)


def test_verify_rejects_wrong_key():
    _assert_rejected(_encode(_claims(), key="some-other-secret-key-" + "z" * 64), pyjwt.InvalidSignatureError)


def test_verify_rejects_token_after_key_rotation(monkeypatch):
    token = create_jwt_access_token({"sub": "operator"})
    monkeypatch.setattr(auth_helper, "JWT_SECRET_KEY", "rotated-secret-key-" + "r" * 64)
    _assert_rejected(token, pyjwt.InvalidSignatureError)


def test_verify_rejects_tampered_payload():
    header, _payload, signature = create_jwt_access_token({"sub": "operator"}).split(".")
    _, forged_payload, _ = _encode(_claims(sub="admin")).split(".")
    _assert_rejected(f"{header}.{forged_payload}.{signature}", pyjwt.InvalidSignatureError)


@pytest.mark.parametrize("algorithm", ["HS384", "HS512"])
def test_verify_rejects_other_algorithms(algorithm):
    _assert_rejected(_encode(_claims(), algorithm=algorithm), pyjwt.InvalidAlgorithmError)


def test_verify_rejects_unsigned_token():
    token = pyjwt.encode(_claims(), key=None, algorithm="none")
    _assert_rejected(token, pyjwt.InvalidAlgorithmError)


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
def test_verify_rejects_malformed_token(token):
    _assert_rejected(token, pyjwt.DecodeError)
