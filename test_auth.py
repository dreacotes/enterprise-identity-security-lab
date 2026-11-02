from time import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

import auth


@pytest.fixture
def token_lab(monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    tenant_id = "11111111-1111-1111-1111-111111111111"
    audience = "22222222-2222-2222-2222-222222222222"
    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

    class LocalKeyClient:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=private_key.public_key())

    monkeypatch.setattr(
        auth,
        "get_auth_config",
        lambda: {
            "tenant_id": tenant_id,
            "audience": audience,
            "issuer": issuer,
            "jwks_client": LocalKeyClient(),
        },
    )

    now = int(time())
    claims = {
        "iss": issuer,
        "aud": audience,
        "tid": tenant_id,
        "ver": "2.0",
        "iat": now - 10,
        "nbf": now - 10,
        "exp": now + 300,
        "roles": ["Resources.Read"],
    }

    return private_key, claims


def test_valid_signed_token_is_accepted(token_lab):
    private_key, claims = token_lab
    token = jwt.encode(claims, private_key, algorithm="RS256")

    result = auth.validate_access_token(token)

    assert result["roles"] == ["Resources.Read"]


def test_token_signed_with_wrong_key_is_rejected(token_lab):
    _, claims = token_lab

    other_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    token = jwt.encode(claims, other_key, algorithm="RS256")

    with pytest.raises(HTTPException) as error:
        auth.validate_access_token(token)

    assert error.value.status_code == 401
    assert error.value.headers["WWW-Authenticate"] == "Bearer"

@pytest.mark.parametrize(
    "claim_name,invalid_value",
    [
        ("exp", 1),
        ("nbf", 4102444800),
        ("iss", "https://unexpected.example"),
        ("aud", "33333333-3333-3333-3333-333333333333"),
        ("tid", "44444444-4444-4444-4444-444444444444"),
        ("ver", "1.0"),
    ],
    ids=[
        "expired",
        "not-yet-valid",
        "wrong-issuer",
        "wrong-audience",
        "wrong-tenant",
        "wrong-version",
    ],
)
def test_invalid_claim_is_rejected(token_lab, claim_name, invalid_value):
    private_key, claims = token_lab
    claims[claim_name] = invalid_value

    token = jwt.encode(claims, private_key, algorithm="RS256")

    with pytest.raises(HTTPException) as error:
        auth.validate_access_token(token)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid or expired access token"