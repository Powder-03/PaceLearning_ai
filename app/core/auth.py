"""
JWT Authentication Module.

Provides JWT-based authentication with email verification support.
"""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(
    scheme_name="JWT",
    description="JWT token for authentication",
    auto_error=True,
)

# JWT Configuration
JWT_SECRET = settings.JWT_SECRET or secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = settings.JWT_EXPIRATION_HOURS


@dataclass
class AuthUser:
    """Authenticated user from JWT."""
    user_id: str
    email: str
    name: Optional[str] = None
    is_verified: bool = False


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = settings.JWT_SECRET or "default-salt"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


def create_access_token(
    user_id: str,
    email: str,
    name: Optional[str] = None,
    is_verified: bool = False,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's unique identifier
        email: User's email
        name: User's display name
        is_verified: Whether email is verified
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "is_verified": is_verified,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    ),
) -> AuthUser:
    """
    Verify JWT and extract user information.
    
    This is a FastAPI dependency that:
    1. Extracts the Bearer token from Authorization header
    2. Verifies the JWT signature
    3. Validates token claims (expiry, etc.)
    4. Returns an AuthUser object with user details
    
    Usage:
        Add `Authorization: Bearer <token>` header to requests
    """
    token = None
    
    # Get token from Authorization header
    if credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please provide a valid Bearer token."
        )
    
    try:
        payload = decode_token(token)
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user information"
            )
        
        return AuthUser(
            user_id=user_id,
            email=email,
            name=payload.get("name"),
            is_verified=payload.get("is_verified", False),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[AuthUser]:
    """
    Optional authentication - returns None if no token provided.
    """
    token = None
    
    if credentials:
        token = credentials.credentials
    
    if not token:
        return None
    
    try:
        return await verify_token(request, credentials)
    except HTTPException:
        return None


async def require_verified_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    ),
) -> AuthUser:
    """
    Require a verified user - raises 403 if email not verified.
    """
    user = await verify_token(request, credentials)
    
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required. Please verify your email to access this resource."
        )
    
    return user


# Aliases for cleaner imports
get_current_user = verify_token
