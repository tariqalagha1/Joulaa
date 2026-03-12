import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.platform_api_key import PlatformAPIKey
from ..schemas.platform_access import PlatformAPIKeyCreate


class PlatformAPIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _generate_raw_key(self) -> str:
        return f"jla_{secrets.token_urlsafe(32)}"

    async def create_key(self, payload: PlatformAPIKeyCreate) -> Tuple[PlatformAPIKey, str]:
        raw_key = self._generate_raw_key()
        key_hash = self._hash_key(raw_key)
        key_prefix = raw_key[:12]

        record = PlatformAPIKey(
            name=payload.name,
            customer_name=payload.customer_name,
            organization_id=payload.organization_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=payload.scopes,
            rate_limit_per_minute=payload.rate_limit_per_minute,
            expires_at=payload.expires_at,
            is_active=True,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record, raw_key

    async def list_keys(self) -> List[PlatformAPIKey]:
        result = await self.db.execute(select(PlatformAPIKey).order_by(PlatformAPIKey.created_at.desc()))
        return list(result.scalars().all())

    async def revoke_key(self, key_id: UUID) -> Optional[PlatformAPIKey]:
        result = await self.db.execute(select(PlatformAPIKey).where(PlatformAPIKey.id == key_id))
        record = result.scalar_one_or_none()
        if not record:
            return None

        record.is_active = False
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def verify_key(self, raw_key: str) -> Optional[PlatformAPIKey]:
        key_hash = self._hash_key(raw_key)
        result = await self.db.execute(
            select(PlatformAPIKey).where(
                PlatformAPIKey.key_hash == key_hash,
                PlatformAPIKey.is_active == True,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        if record.expires_at and record.expires_at < datetime.now(timezone.utc):
            return None

        record.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(record)
        return record
