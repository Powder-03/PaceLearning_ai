"""
Clerk Authentication Module.

Provides JWT validation for Clerk-authenticated requests.
Frontend will use Clerk SDK to get tokens, backend validates them here.
"""
import logging
from typing import Optional
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(
    scheme_name="Clerk JWT",
    description="JWT token from Clerk authentication",
    auto_error=True,
)

# Cache for JWKS client
_jwks_client: Optional[PyJWKClient] = None


@dataclass
class ClerkUser:
    """Authenticated user from Clerk JWT."""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "User"


def get_jwks_client() -> PyJWKClient:
    """
    Get or create JWKS client for Clerk.
    
    Clerk's JWKS endpoint is used to verify JWT signatures.
    """
    global _jwks_client
    
    if _jwks_client is None:
        if not settings.CLERK_JWKS_URL:
            raise HTTPException(
                status_code=500,
                detail="Clerk JWKS URL not configured"
            )
        _jwks_client = PyJWKClient(
            settings.CLERK_JWKS_URL,
            cache_keys=True,
            lifespan=3600,  # Cache keys for 1 hour
        )
    
    return _jwks_client


async def verify_clerk_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> ClerkUser:
    """
    Verify Clerk JWT and extract user information.
    
    This is a FastAPI dependency that:
    1. Extracts the Bearer token from Authorization header
    2. Verifies the JWT signature using Clerk's JWKS
    3. Validates token claims (expiry, issuer, etc.)
    4. Returns a ClerkUser object with user details
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: ClerkUser = Depends(verify_clerk_token)):
            return {"user_id": user.user_id}
    """
    token = credentials.credentials
    
    try:
        # Get the signing key from Clerk's JWKS
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_aud": False,  # Clerk doesn't always set audience
                "verify_iss": True,
            },
            issuer=settings.CLERK_ISSUER,
        )
        
        # Extract user information from Clerk JWT claims
        # Clerk uses 'sub' for user ID
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )
        
        # Extract additional claims (if present)
        # These may be in the token or need to be fetched from Clerk API
        return ClerkUser(
            user_id=user_id,
            email=payload.get("email"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            image_url=payload.get("image_url"),
        )
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidIssuerError:
        logger.warning("Invalid JWT issuer")
        raise HTTPException(
            status_code=401,
            detail="Invalid token issuer"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.exception(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[ClerkUser]:
    """
    Optional authentication - returns None if no token provided.
    
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if credentials is None:
        return None
    
    try:
        return await verify_clerk_token(credentials)
    except HTTPException:
        return None


# Alias for cleaner imports
get_current_user = verify_clerk_token
