from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExternalAPISettingCreate(BaseModel):
    service_name: str
    base_url: str
    auth_type: str = "api_key"
    api_key_secret: Optional[str] = None
    default_headers: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    organization_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExternalAPISettingResponse(BaseModel):
    id: UUID
    service_name: str
    base_url: str
    auth_type: str
    has_api_key_secret: bool
    default_headers: Dict[str, Any]
    timeout_seconds: int
    is_active: bool
    organization_id: Optional[UUID]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PlatformAPIKeyCreate(BaseModel):
    name: str
    customer_name: str
    organization_id: Optional[UUID] = None
    scopes: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    expires_at: Optional[datetime] = None


class PlatformAPIKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    customer_name: str
    key_prefix: str
    api_key: str
    scopes: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    is_active: bool


class PlatformAPIKeyResponse(BaseModel):
    id: UUID
    name: str
    customer_name: str
    key_prefix: str
    scopes: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
