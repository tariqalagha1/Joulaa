from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.external_api_setting import ExternalAPISetting
from ..schemas.platform_access import ExternalAPISettingCreate


class ExternalAPISettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_setting(self, payload: ExternalAPISettingCreate) -> ExternalAPISetting:
        record = ExternalAPISetting(
            service_name=payload.service_name,
            base_url=payload.base_url,
            auth_type=payload.auth_type,
            api_key_secret=payload.api_key_secret,
            default_headers=payload.default_headers,
            timeout_seconds=payload.timeout_seconds,
            organization_id=payload.organization_id,
            metadata_=payload.metadata,
            is_active=True,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_settings(self) -> List[ExternalAPISetting]:
        result = await self.db.execute(
            select(ExternalAPISetting).where(ExternalAPISetting.is_active == True).order_by(ExternalAPISetting.created_at.desc())
        )
        return list(result.scalars().all())
