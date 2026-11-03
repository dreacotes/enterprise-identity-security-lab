import os
from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError


@lru_cache
def get_auth_config():
    try:
        tenant_id = str(UUID(os.environ["ENTRA_TENANT_ID"]))
        audience = str(UUID(os.environ["ENTRA_AUDIENCE"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Authentication service is not configured correctly",
        ) from exc    

    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
    jwks_url = (
        f"https://login.microsoftonline.com/{tenant_id}"
        "/discovery/v2.0/keys"
    )

    return {
        "tenant_id": tenant_id,
        "audience": audience,
        "issuer": issuer,
        "jwks_client": PyJWKClient(jwks_url, timeout=5),
    }


def validate_access_token(token: str):
    config = get_auth_config()

    try:
        signing_key = config["jwks_client"].get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config["audience"],
            issuer=config["issuer"],
            options={
                "require": ["exp", "iat", "nbf", "iss", "aud", "tid", "ver"],
            },
        )

        if (
            claims["tid"] != config["tenant_id"]
            or claims["ver"] != "2.0"
        ):
            raise jwt.InvalidTokenError("Unexpected tenant or token version")

        return claims

    except PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="Token verification service unavailable",
        ) from exc

    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

bearer_scheme = HTTPBearer(auto_error=False)


def require_resources_read(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = validate_access_token(credentials.credentials)

    if "scp" in claims:
        scopes = claims["scp"]

        if (
            not isinstance(scopes, str)
            or "Resources.Read.Delegated" not in scopes.split()
        ):
            raise HTTPException(
                status_code=403,
                detail="Resources.Read.Delegated permission required",
            )

        return claims

    roles = claims.get("roles", [])
    if not isinstance(roles, list) or "Resources.Read" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Resources.Read permission required",
        )

    return claims