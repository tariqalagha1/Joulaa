"""Authentication and authorization utilities for Joulaa platform"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from .config import settings
from ..database import get_db
from ..models.organization import UserOrganization
from ..models.user import User
from .exceptions import (
    AuthenticationError, AuthorizationError, TokenExpiredError,
    InvalidTokenError, UserNotFoundError
)

logger = structlog.get_logger()
security = HTTPBearer()


class TokenManager:
    """Manages JWT tokens for authentication"""
    
    @staticmethod
    def create_access_token(
        user_id: UUID,
        organization_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_id),
            "org_id": str(organization_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        organization_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new refresh token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "org_id": str(organization_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check if token has expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise TokenExpiredError()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError:
            raise InvalidTokenError()
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise InvalidTokenError()
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """Create a new access token from a refresh token"""
        payload = TokenManager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
        
        user_id = UUID(payload.get("sub"))
        organization_id = UUID(payload.get("org_id"))
        
        return TokenManager.create_access_token(user_id, organization_id)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    try:
        # Verify token
        payload = TokenManager.verify_token(credentials.credentials)
        
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        user_id = UUID(payload.get("sub"))
        
        # Get user from database
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError()
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
        
    except (TokenExpiredError, InvalidTokenError, UserNotFoundError):
        raise
    except Exception as e:
        logger.error("Authentication failed", error=str(e), exc_info=True)
        raise AuthenticationError()


async def get_current_organization(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Get current organization ID from token, with legacy-token fallback."""
    try:
        payload = TokenManager.verify_token(credentials.credentials)

        if payload.get("type") == "access" and payload.get("org_id"):
            return UUID(payload.get("org_id"))

        # Backward compatibility for legacy tokens that only include "sub".
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise InvalidTokenError("Missing subject in token")

        user_id = UUID(user_id_raw)
        membership_query = (
            select(UserOrganization.organization_id)
            .where(
                UserOrganization.user_id == user_id,
                UserOrganization.is_active == True,  # noqa: E712
            )
            .order_by(UserOrganization.joined_at.asc())
            .limit(1)
        )
        membership_result = await db.execute(membership_query)
        organization_id = membership_result.scalar_one_or_none()
        if organization_id is None:
            raise AuthenticationError("No active organization membership found")
        return organization_id

    except (TokenExpiredError, InvalidTokenError):
        raise
    except Exception as e:
        logger.error("Organization extraction failed", error=str(e))
        raise AuthenticationError()


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user (additional check)"""
    if not current_user.is_active:
        raise AuthenticationError("User account is disabled")
    return current_user


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Get user from token string (for WebSocket authentication)"""
    try:
        payload = TokenManager.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
            
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            return None
            
        return user
        
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, ValueError):
        return None
    except Exception as e:
        logger.error("Error getting user from token", error=str(e))
        return None


class PermissionChecker:
    """Utility class for checking user permissions"""
    
    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required permissions"""
        # For now, implement basic role-based access
        # In a real implementation, this would check against a proper RBAC system
        
        user_permissions = self._get_user_permissions(current_user)
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise AuthorizationError(
                    f"Missing required permission: {permission}"
                )
        
        return current_user
    
    def _get_user_permissions(self, user: User) -> list:
        """Get user permissions based on role"""
        # Basic role-based permissions
        role_permissions = {
            "admin": [
                "read:agents", "write:agents", "delete:agents",
                "read:users", "write:users", "delete:users",
                "read:organizations", "write:organizations",
                "read:analytics", "write:analytics",
                "manage:integrations", "manage:billing"
            ],
            "manager": [
                "read:agents", "write:agents",
                "read:users", "write:users",
                "read:analytics",
                "manage:integrations"
            ],
            "user": [
                "read:agents", "write:agents",
                "read:analytics"
            ],
            "viewer": [
                "read:agents",
                "read:analytics"
            ]
        }
        
        # Get user role (this would come from user model or organization membership)
        user_role = getattr(user, 'role', 'user')
        return role_permissions.get(user_role, [])


# Permission dependency factories
def require_permissions(*permissions):
    """Create a permission dependency"""
    return PermissionChecker(list(permissions))


# Common permission dependencies
require_agent_read = require_permissions("read:agents")
require_agent_write = require_permissions("write:agents")
require_agent_delete = require_permissions("delete:agents")
require_user_management = require_permissions("write:users")
require_admin = require_permissions("manage:organizations")
require_analytics = require_permissions("read:analytics")


class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check rate limits for user"""
        now = datetime.utcnow()
        user_key = str(current_user.id)
        
        # Clean old requests
        if user_key in self.requests:
            self.requests[user_key] = [
                req_time for req_time in self.requests[user_key]
                if (now - req_time).total_seconds() < self.window_seconds
            ]
        else:
            self.requests[user_key] = []
        
        # Check if limit exceeded
        if len(self.requests[user_key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Add current request
        self.requests[user_key].append(now)
        
        return current_user


# Rate limiting dependencies
rate_limit_standard = RateLimiter(max_requests=100, window_seconds=60)  # 100 requests per minute
rate_limit_strict = RateLimiter(max_requests=10, window_seconds=60)     # 10 requests per minute
rate_limit_ai_chat = RateLimiter(max_requests=20, window_seconds=60)    # 20 AI requests per minute


class APIKeyAuth:
    """API Key authentication for external integrations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate using API key"""
        # This would check against an API keys table
        # For now, return None (not implemented)
        return None


def create_api_key_dependency():
    """Create API key authentication dependency"""
    async def api_key_auth(
        api_key: str,
        db: AsyncSession = Depends(get_db)
    ) -> Dict[str, Any]:
        auth = APIKeyAuth(db)
        result = await auth.authenticate_api_key(api_key)
        
        if not result:
            raise AuthenticationError("Invalid API key")
        
        return result
    
    return api_key_auth


# Security utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_api_key() -> str:
    """Generate a secure API key"""
    import secrets
    return f"joulaa_{secrets.token_urlsafe(32)}"


def generate_reset_token() -> str:
    """Generate a password reset token"""
    import secrets
    return secrets.token_urlsafe(32)
