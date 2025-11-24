"""
Authentication middleware for FastAPI
Validates Supabase JWT tokens and enforces role-based access
"""

import logging
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient
from jose import jwt as jose_jwt

from app.config import settings

security = HTTPBearer()

logger = logging.getLogger(__name__)

# Cache for JWK client (Supabase public keys)
_jwk_client: Optional[PyJWKClient] = None


def get_jwk_client() -> PyJWKClient:
    """Get or create JWK client for Supabase"""
    global _jwk_client
    if _jwk_client is None:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL is not configured; cannot resolve JWKS")
        jwks_url = f"{settings.supabase_url}/.well-known/jwks.json"
        _jwk_client = PyJWKClient(jwks_url)
    return _jwk_client


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify Supabase JWT token and return decoded payload
    
    Raises HTTPException if token is invalid
    """
    token = credentials.credentials
    
    last_error: Optional[Exception] = None

    # Preferred path: HS256 using Supabase JWT secret (default hosted Supabase behavior)
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload
        except Exception as error:  # noqa: BLE001
            last_error = error
            logger.warning("HS256 Supabase JWT verification failed: %s", error)

    # Fallback path: RS256 via JWKS (self-hosted Supabase or custom GoTrue)
    signing_key = None
    try:
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError as error:
        logger.info("Token expired: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from error
    except jwt.InvalidTokenError as error:
        logger.error("Invalid token error: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(error)}",
        ) from error
    except Exception as error:  # noqa: BLE001
        logger.error("Token verification exception: %s", error)
        # Fallback: try with jose if PyJWT fails (maintain legacy behavior)
        if signing_key is not None:
            try:
                payload = jose_jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience="authenticated",
                    options={"verify_exp": True},
                )
                return payload
            except Exception as jose_error:  # noqa: BLE001
                logger.error("Token verification failed via jose: %s", jose_error)
                # Prefer HS256 error message if that was the root cause
                if last_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Token verification failed: {last_error}",
                    ) from jose_error
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token verification failed: {jose_error}",
                ) from jose_error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed: Unable to resolve signing key",
        ) from error


def get_user_role(email: str) -> Optional[str]:
    """
    Determine user role based on email domain
    
    Returns: 'student', 'admin', or None
    """
    if not email:
        return None
    
    if email.endswith("@my.centennialcollege.ca"):
        return "student"
    
    if email.endswith("@centennialcollege.ca"):
        return "admin"
    
    return None


def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Require authentication and return user info
    
    Returns dict with:
    - user_id: UUID from token
    - email: User email
    - role: 'student' or 'admin'
    """
    payload = verify_token(credentials)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    role = get_user_role(email)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institutional Email Required",
        )
    
    return {
        "user_id": user_id,
        "email": email,
        "role": role,
    }


def require_admin(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Require admin role
    
    Raises HTTPException if user is not an admin
    """
    user_info = require_auth(credentials)
    
    if user_info["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user_info


def require_student(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Require student role
    
    Raises HTTPException if user is not a student
    """
    user_info = require_auth(credentials)
    
    if user_info["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    
    return user_info

