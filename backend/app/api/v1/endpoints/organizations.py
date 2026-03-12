from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....core.auth_dependency import get_current_user
from ....models.user import User
from ....services.organization_service import OrganizationService
from ....schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationDetailResponse, OrganizationListResponse,
    OrganizationMemberCreate, OrganizationMemberUpdate,
    OrganizationMemberResponse, OrganizationStats
)
from ....core.exceptions import (
    OrganizationNotFoundError, OrganizationPermissionError,
    OrganizationValidationError, UserNotFoundError
)

router = APIRouter()


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    subscription_plan: Optional[str] = Query(None, description="Filter by subscription plan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List organizations user is member of"""
    try:
        org_service = OrganizationService(db)
        return await org_service.list_organizations(
            requesting_user_id=current_user.id,
            search=search,
            is_active=is_active,
            subscription_plan=subscription_plan,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}"
        )


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organization"""
    try:
        org_service = OrganizationService(db)
        return await org_service.create_organization(
            org_data=org_data,
            created_by=current_user.id
        )
    except OrganizationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/{organization_id}", response_model=OrganizationDetailResponse)
async def get_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization by ID"""
    try:
        org_service = OrganizationService(db)
        return await org_service.get_organization(
            organization_id=organization_id,
            requesting_user_id=current_user.id
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}"
        )


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    org_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization"""
    try:
        org_service = OrganizationService(db)
        return await org_service.update_organization(
            organization_id=organization_id,
            org_data=org_data,
            requesting_user_id=current_user.id
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OrganizationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) vs hard delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete organization (owner only)"""
    try:
        org_service = OrganizationService(db)
        await org_service.delete_organization(
            organization_id=organization_id,
            requesting_user_id=current_user.id,
            soft_delete=soft_delete
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )


@router.post("/{organization_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    organization_id: UUID,
    member_data: OrganizationMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add member to organization"""
    try:
        org_service = OrganizationService(db)
        return await org_service.add_member(
            organization_id=organization_id,
            member_data=member_data,
            requesting_user_id=current_user.id
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OrganizationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove member from organization"""
    try:
        org_service = OrganizationService(db)
        await org_service.remove_member(
            organization_id=organization_id,
            user_id=user_id,
            requesting_user_id=current_user.id
        )
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OrganizationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def list_members(
    organization_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List organization members"""
    try:
        org_service = OrganizationService(db)
        # First check access
        await org_service._check_organization_access(organization_id, current_user.id)
        
        # Get organization details which includes members
        org_detail = await org_service.get_organization(
            organization_id=organization_id,
            requesting_user_id=current_user.id
        )
        
        members = org_detail.members or []
        
        # Apply filters
        if is_active is not None:
            # This would need to be implemented in the service
            pass
        
        if role:
            members = [m for m in members if m.get("role") == role]
        
        # Convert to response format
        member_responses = [
            OrganizationMemberResponse(
                user_id=member["user_id"],
                organization_id=organization_id,
                role=member["role"],
                is_active=True,  # Assuming active since we filter in service
                joined_at=member["joined_at"],
                user=member.get("user")
            )
            for member in members
        ]
        
        return member_responses
        
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list members: {str(e)}"
        )


@router.put("/{organization_id}/members/{user_id}", response_model=OrganizationMemberResponse)
async def update_member(
    organization_id: UUID,
    user_id: UUID,
    member_data: OrganizationMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization member"""
    try:
        # Check permissions
        org_service = OrganizationService(db)
        await org_service._check_organization_permissions(
            organization_id, current_user.id, "manage_members"
        )
        
        # Update member
        update_data = {}
        if member_data.role is not None:
            update_data["role"] = member_data.role
        if member_data.is_active is not None:
            update_data["is_active"] = member_data.is_active
        
        if update_data:
            from sqlalchemy import update
            from ....models.organization import UserOrganization
            from sqlalchemy import and_
            
            update_query = update(UserOrganization).where(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id
                )
            ).values(**update_data)
            
            result = await db.execute(update_query)
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
        
        # Get updated member
        from sqlalchemy import select
        from ....models.organization import UserOrganization
        
        query = select(UserOrganization).where(
            and_(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        return OrganizationMemberResponse(
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            role=membership.role,
            is_active=membership.is_active,
            joined_at=membership.joined_at
        )
        
    except OrganizationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OrganizationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member: {str(e)}"
        )
