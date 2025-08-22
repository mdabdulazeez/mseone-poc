from typing import Dict, Optional
from functools import lru_cache
from datetime import datetime, timezone

import requests
import jwt
from fastapi import Request, HTTPException, status

from config.settings import get_settings


@lru_cache(maxsize=1)
def _get_openid_config_url() -> str:
    settings = get_settings()
    authority = settings.AZURE_AD_AUTHORITY.rstrip("/")
    return f"{authority}/v2.0/.well-known/openid-configuration"


@lru_cache(maxsize=1)
def _get_jwks_uri() -> str:
    resp = requests.get(_get_openid_config_url(), timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Failed to load OpenID configuration")
    return resp.json().get("jwks_uri")


@lru_cache(maxsize=1)
def _get_jwks() -> Dict:
    resp = requests.get(_get_jwks_uri(), timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Failed to load JWKS")
    return resp.json()


def _get_signing_key(token: str):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Cache miss: refresh JWKS and try once more
    _get_jwks.cache_clear()
    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")


async def get_current_user(request: Request) -> Dict[str, object]:
    """Validate Azure AD JWT from Authorization header and return user claims.

    Expected header: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = auth_header.split(" ", 1)[1].strip()
    settings = get_settings()

    try:
        signing_key = _get_signing_key(token)

        options = {"verify_aud": True, "verify_signature": True, "verify_exp": True, "verify_iss": True}
        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.AZURE_AD_AUDIENCE,
            issuer=f"{settings.AZURE_AD_AUTHORITY.rstrip('/')}/v2.0",
            options=options,
        )

        # Basic shape of returned user dict
        preferred_username = (
            decoded.get("preferred_username")
            or decoded.get("upn")
            or decoded.get("email")
            or decoded.get("oid")
        )
        roles = decoded.get("roles") or decoded.get("scp", "").split() if decoded.get("scp") else []

        return {
            "preferred_username": preferred_username,
            "roles": roles,
            "claims": decoded,
            "token_exp": decoded.get("exp"),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


