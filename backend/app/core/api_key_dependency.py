from typing import Any, Dict

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.platform_api_key_service import PlatformAPIKeyService


async def require_platform_api_key(
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header",
        )

    service = PlatformAPIKeyService(db)
    record = await service.verify_key(x_api_key)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    return {
        "id": str(record.id),
        "name": record.name,
        "customer_name": record.customer_name,
        "key_prefix": record.key_prefix,
    }
