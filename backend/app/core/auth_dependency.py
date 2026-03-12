"""Centralized auth dependency shim for route handlers.

Uses the async canonical auth dependency first and falls back to legacy
token verification so existing login-issued tokens continue to work.
"""

from uuid import UUID

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from .auth import get_current_user as canonical_get_current_user, security
from .exceptions import AuthenticationError
from .security import verify_token as legacy_verify_token

logger = structlog.get_logger()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Canonical route dependency with legacy-token compatibility."""
    try:
        return await canonical_get_current_user(credentials=credentials, db=db)
    except Exception as canonical_error:
        payload = legacy_verify_token(credentials.credentials)
        if payload is None:
            raise canonical_error

        user_id = payload.get("sub")
        if user_id is None:
            raise canonical_error

        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User account is disabled")

        logger.info("Authenticated using legacy token compatibility path", user_id=str(user.id))
        return user
