"""
Experiment 4: Authentication — API Key & JWT
=============================================
- API Key authentication via X-API-Key header
- JWT bearer-token authentication
- Secure the /predict endpoint with either method
"""

import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Header, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt


# --------------- Configuration ---------------

# Secret used to sign JWTs (override via env var in production)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30

# Valid API keys (in production, store hashed keys in a database)
VALID_API_KEYS: set[str] = {
    os.getenv("API_KEY", "mlops-demo-key-2024"),
}

bearer_scheme = HTTPBearer(auto_error=False)


# --------------- JWT helpers ---------------

def create_jwt_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )


# --------------- Dependency functions ---------------

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """Validate the API key supplied in X-API-Key header."""
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Validate a Bearer JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    return decode_jwt_token(credentials.credentials)


def verify_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """
    Accept EITHER an API key OR a JWT bearer token.
    At least one must be valid for the request to proceed.
    """
    # Try API key first
    if x_api_key and x_api_key in VALID_API_KEYS:
        return f"api_key:{x_api_key[:8]}..."

    # Try JWT
    if credentials:
        payload = decode_jwt_token(credentials.credentials)
        return f"jwt:{payload.get('sub', 'unknown')}"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a valid X-API-Key header or Bearer token",
    )
