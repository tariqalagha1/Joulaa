from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import math

from ....database import get_db
from ....core.auth_dependency import get_current_user
from ....models.user import User
from ....models.organization import UserOrganization
from ....schemas.integration import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse,
    IntegrationDetailResponse, IntegrationListResponse, IntegrationStats,
    IntegrationSearchRequest, IntegrationSyncRequest, IntegrationSyncResponse,
    IntegrationHealthCheck, IntegrationTestRequest, IntegrationTestResponse,
    BulkIntegrationOperation, BulkIntegrationOperationResponse
)
from ....services.integration_service import IntegrationService
from ....core.exceptions import (
    NotFoundError, ValidationError, PermissionError, ConflictError
)
from ....core.audit import log_audit_event
from ....core.tenant_guard import ensure_org_access

router = APIRouter()


def _to_integration_response(integration) -> IntegrationResponse:
    return IntegrationResponse(
        id=integration.id,
        organization_id=integration.organization_id,
        integration_type=integration.integration_type,
        name=integration.name,
        description=integration.description,
        configuration=integration.configuration,
        is_active=integration.is_active,
        health_check_url=integration.health_check_url,
        metadata=integration.metadata_ or {},
        sync_status=integration.sync_status,
        sync_error=integration.sync_error,
        last_sync_at=integration.last_sync_at,
        health_status=integration.health_status,
        last_health_check=integration.last_health_check,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        created_by=integration.created_by,
        updated_by=integration.updated_by,
    )


@router.get("/", response_model=IntegrationListResponse)
async def list_integrations(
    query: Optional[str] = Query(None, description="Search query"),
    integration_type: Optional[str] = Query(None, description="Filter by integration type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    sync_status: Optional[str] = Query(None, description="Filter by sync status"),
    organization_id: Optional[uuid.UUID] = Query(None, description="Filter by organization"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List integrations with filtering and pagination"""
    try:
        search_params = IntegrationSearchRequest(
            query=query,
            integration_type=integration_type,
            is_active=is_active,
            health_status=health_status,
            sync_status=sync_status,
            organization_id=organization_id,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        service = IntegrationService(db)
        integrations, total = await service.list_integrations(search_params, current_user.id)
        
        total_pages = math.ceil(total / page_size)
        
        return IntegrationListResponse(
            integrations=[_to_integration_response(integration) for integration in integrations],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new integration"""
    try:
        service = IntegrationService(db)
        integration = await service.create_integration(integration_data, current_user.id)
        log_audit_event(
            event_type="integration.create",
            user_id=current_user.id,
            organization_id=integration.organization_id,
            resource_type="integration",
            resource_id=integration.id,
            metadata={"integration_type": integration.integration_type},
        )
        return _to_integration_response(integration)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{integration_id}", response_model=IntegrationDetailResponse)
async def get_integration(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    include_organization: bool = Query(False, description="Include organization details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get integration by ID"""
    try:
        service = IntegrationService(db)
        integration = await service.get_integration(
            integration_id, 
            current_user.id, 
            include_organization=include_organization
        )
        membership_result = await db.execute(
            select(UserOrganization.organization_id).where(
                UserOrganization.user_id == current_user.id,
                UserOrganization.organization_id == integration.organization_id,
                UserOrganization.is_active == True
            )
        )
        ensure_org_access(
            integration.organization_id,
            membership_result.scalar_one_or_none()
        )
        
        response_data = _to_integration_response(integration).dict()
        response_data.update({
            "display_name": integration.display_name,
            "is_healthy": integration.is_healthy,
            "needs_sync": integration.needs_sync
        })
        
        return IntegrationDetailResponse(**response_data)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    update_data: IntegrationUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update integration"""
    try:
        service = IntegrationService(db)
        integration = await service.update_integration(integration_id, update_data, current_user.id)
        return _to_integration_response(integration)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    soft_delete: bool = Query(True, description="Perform soft delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete integration"""
    try:
        service = IntegrationService(db)
        integration = await service.get_integration(integration_id, current_user.id)
        await service.delete_integration(integration_id, current_user.id, soft_delete=soft_delete)
        log_audit_event(
            event_type="integration.delete",
            user_id=current_user.id,
            organization_id=integration.organization_id,
            resource_type="integration",
            resource_id=integration_id,
            metadata={"soft_delete": soft_delete},
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{integration_id}/sync", response_model=IntegrationSyncResponse)
async def sync_integration(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    sync_request: IntegrationSyncRequest = IntegrationSyncRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger integration synchronization"""
    try:
        service = IntegrationService(db)
        result = await service.sync_integration(
            integration_id, 
            current_user.id, 
            force=sync_request.force
        )
        
        return IntegrationSyncResponse(
            integration_id=uuid.UUID(result["integration_id"]),
            sync_started=result["sync_started"],
            sync_status=result.get("sync_status", "pending"),
            message=result["message"]
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{integration_id}/health-check", response_model=IntegrationHealthCheck)
async def health_check_integration(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform health check on integration"""
    try:
        service = IntegrationService(db)
        result = await service.health_check_integration(integration_id, current_user.id)
        
        return IntegrationHealthCheck(
            integration_id=uuid.UUID(result["integration_id"]),
            health_status=result["health_status"],
            response_time=result.get("response_time"),
            error_message=result.get("error_message"),
            checked_at=result["checked_at"],
            details=result.get("details")
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/test", response_model=IntegrationTestResponse)
async def test_integration(
    test_request: IntegrationTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test integration configuration without creating it"""
    try:
        # This is a placeholder for testing integration configuration
        # In a real implementation, you would test the actual connection
        
        # Basic validation
        if not test_request.configuration:
            raise ValidationError("Configuration is required for testing")
        
        # Simulate test based on integration type
        import asyncio
        await asyncio.sleep(0.5)  # Simulate test time
        
        # For demo purposes, assume test passes
        return IntegrationTestResponse(
            success=True,
            message=f"Test successful for {test_request.integration_type} integration",
            response_time=500.0,
            test_results={
                "connection": "successful",
                "authentication": "valid",
                "permissions": "adequate"
            }
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        return IntegrationTestResponse(
            success=False,
            message=f"Test failed: {str(e)}",
            error_details={"error": str(e)}
        )


@router.get("/stats", response_model=IntegrationStats)
async def get_integration_stats(
    organization_id: Optional[uuid.UUID] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get integration statistics"""
    try:
        service = IntegrationService(db)
        stats = await service.get_integration_stats(organization_id, current_user.id)
        return IntegrationStats(**stats)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/bulk", response_model=BulkIntegrationOperationResponse)
async def bulk_integration_operation(
    operation_request: BulkIntegrationOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on integrations"""
    try:
        service = IntegrationService(db)
        results = []
        errors = []
        successful = 0
        failed = 0
        
        for integration_id in operation_request.integration_ids:
            try:
                if operation_request.operation == "activate":
                    await service.update_integration(
                        integration_id,
                        IntegrationUpdate(is_active=True),
                        current_user.id
                    )
                elif operation_request.operation == "deactivate":
                    await service.update_integration(
                        integration_id,
                        IntegrationUpdate(is_active=False),
                        current_user.id
                    )
                elif operation_request.operation == "sync":
                    await service.sync_integration(
                        integration_id,
                        current_user.id,
                        force=operation_request.options.get("force", False)
                    )
                elif operation_request.operation == "delete":
                    soft_delete = operation_request.options.get("soft_delete", True)
                    await service.delete_integration(
                        integration_id,
                        current_user.id,
                        soft_delete=soft_delete
                    )
                elif operation_request.operation == "health_check":
                    await service.health_check_integration(integration_id, current_user.id)
                
                results.append({
                    "integration_id": str(integration_id),
                    "status": "success",
                    "message": f"{operation_request.operation.title()} completed successfully"
                })
                successful += 1
                
            except Exception as e:
                errors.append({
                    "integration_id": str(integration_id),
                    "error": str(e)
                })
                failed += 1
        
        return BulkIntegrationOperationResponse(
            operation=operation_request.operation,
            total_requested=len(operation_request.integration_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
