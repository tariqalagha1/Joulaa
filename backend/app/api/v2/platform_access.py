from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.audit import log_audit_event
from ...core.auth_dependency import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.platform_access import (
    ExternalAPISettingCreate,
    ExternalAPISettingResponse,
    PlatformAPIKeyCreate,
    PlatformAPIKeyCreateResponse,
    PlatformAPIKeyResponse,
)
from ...services.external_api_settings_service import ExternalAPISettingsService
from ...services.platform_api_key_service import PlatformAPIKeyService

router = APIRouter()


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )


@router.post("/external-api-settings", response_model=ExternalAPISettingResponse, status_code=status.HTTP_201_CREATED)
async def create_external_api_setting(
    payload: ExternalAPISettingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExternalAPISettingResponse:
    _require_admin(current_user)
    service = ExternalAPISettingsService(db)
    record = await service.create_setting(payload)
    log_audit_event(
        event_type="external_api_setting.create",
        user_id=current_user.id,
        organization_id=record.organization_id,
        resource_type="external_api_setting",
        resource_id=record.id,
        metadata={
            "service_name": record.service_name,
            "base_url": record.base_url,
            "auth_type": record.auth_type,
        },
    )
    return ExternalAPISettingResponse(
        id=record.id,
        service_name=record.service_name,
        base_url=record.base_url,
        auth_type=record.auth_type,
        has_api_key_secret=bool(record.api_key_secret),
        default_headers=record.default_headers,
        timeout_seconds=record.timeout_seconds,
        is_active=record.is_active,
        organization_id=record.organization_id,
        metadata=record.metadata_ or {},
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/external-api-settings", response_model=List[ExternalAPISettingResponse])
async def list_external_api_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ExternalAPISettingResponse]:
    _require_admin(current_user)
    service = ExternalAPISettingsService(db)
    records = await service.list_settings()
    return [
        ExternalAPISettingResponse(
            id=record.id,
            service_name=record.service_name,
            base_url=record.base_url,
            auth_type=record.auth_type,
            has_api_key_secret=bool(record.api_key_secret),
            default_headers=record.default_headers,
            timeout_seconds=record.timeout_seconds,
            is_active=record.is_active,
            organization_id=record.organization_id,
            metadata=record.metadata_ or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in records
    ]


@router.post("/api-keys", response_model=PlatformAPIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_platform_api_key(
    payload: PlatformAPIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlatformAPIKeyCreateResponse:
    _require_admin(current_user)
    service = PlatformAPIKeyService(db)
    record, raw_key = await service.create_key(payload)
    log_audit_event(
        event_type="platform_api_key.create",
        user_id=current_user.id,
        organization_id=record.organization_id,
        resource_type="platform_api_key",
        resource_id=record.id,
        metadata={
            "name": record.name,
            "customer_name": record.customer_name,
            "key_prefix": record.key_prefix,
            "scopes": record.scopes,
            "rate_limit_per_minute": record.rate_limit_per_minute,
        },
    )
    return PlatformAPIKeyCreateResponse(
        id=record.id,
        name=record.name,
        customer_name=record.customer_name,
        key_prefix=record.key_prefix,
        api_key=raw_key,
        scopes=record.scopes,
        rate_limit_per_minute=record.rate_limit_per_minute,
        expires_at=record.expires_at,
        is_active=record.is_active,
    )


@router.get("/api-keys", response_model=List[PlatformAPIKeyResponse])
async def list_platform_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PlatformAPIKeyResponse]:
    _require_admin(current_user)
    service = PlatformAPIKeyService(db)
    records = await service.list_keys()
    return [
        PlatformAPIKeyResponse(
            id=record.id,
            name=record.name,
            customer_name=record.customer_name,
            key_prefix=record.key_prefix,
            scopes=record.scopes,
            rate_limit_per_minute=record.rate_limit_per_minute,
            expires_at=record.expires_at,
            last_used_at=record.last_used_at,
            is_active=record.is_active,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in records
    ]


@router.post("/api-keys/{key_id}/revoke", response_model=PlatformAPIKeyResponse)
async def revoke_platform_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlatformAPIKeyResponse:
    _require_admin(current_user)
    service = PlatformAPIKeyService(db)
    record = await service.revoke_key(key_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    log_audit_event(
        event_type="platform_api_key.revoke",
        user_id=current_user.id,
        organization_id=record.organization_id,
        resource_type="platform_api_key",
        resource_id=record.id,
        metadata={"key_prefix": record.key_prefix, "customer_name": record.customer_name},
    )

    return PlatformAPIKeyResponse(
        id=record.id,
        name=record.name,
        customer_name=record.customer_name,
        key_prefix=record.key_prefix,
        scopes=record.scopes,
        rate_limit_per_minute=record.rate_limit_per_minute,
        expires_at=record.expires_at,
        last_used_at=record.last_used_at,
        is_active=record.is_active,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
