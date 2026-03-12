from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.auth_dependency import get_current_user
from ....models.user import User
from ....services.user_service import UserService
from ....schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserDetailResponse,
    UserListResponse, UserPreferences, UserStats, BulkUserOperation,
    BulkUserOperationResponse
)
from ....core.exceptions import (
    UserNotFoundError, ValidationError, AuthenticationError
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List users with filtering and pagination"""
    try:
        user_service = UserService(db)
        return await user_service.list_users(
            requesting_user_id=current_user.id,
            organization_id=organization_id,
            role=role,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    try:
        user_service = UserService(db)
        return await user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name_ar=user_data.full_name_ar,
            full_name_en=user_data.full_name_en,
            language_preference=user_data.language_preference,
            timezone=user_data.timezone
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user organizations
        organizations = await user_service.get_user_organizations(user.id)
        
        return UserDetailResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name_ar=user.full_name_ar,
            full_name_en=user.full_name_en,
            display_name=user.display_name,
            language_preference=user.language_preference,
            timezone=user.timezone,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            organizations=[{
                "id": org.id,
                "name_ar": org.name_ar,
                "name_en": org.name_en,
                "role": "member"  # This would come from OrganizationMember relationship
            } for org in organizations],
            preferences={
                "notification_preferences": user.notification_preferences,
                "ui_preferences": user.ui_preferences
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(
            user_id=current_user.id,
            user_data=user_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            full_name_ar=updated_user.full_name_ar,
            full_name_en=updated_user.full_name_en,
            display_name=updated_user.display_name,
            language_preference=updated_user.language_preference,
            timezone=updated_user.timezone,
            role=updated_user.role,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            avatar_url=updated_user.avatar_url,
            bio=updated_user.bio,
            phone_number=updated_user.phone_number,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            last_login=updated_user.last_login
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions (users can view their own profile, admins can view all)
        if user.id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user"
            )
        
        # Get user organizations
        organizations = await user_service.get_user_organizations(user.id)
        
        return UserDetailResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name_ar=user.full_name_ar,
            full_name_en=user.full_name_en,
            display_name=user.display_name,
            language_preference=user.language_preference,
            timezone=user.timezone,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            organizations=[{
                "id": org.id,
                "name_ar": org.name_ar,
                "name_en": org.name_en,
                "role": "member"
            } for org in organizations],
            preferences={
                "notification_preferences": user.notification_preferences,
                "ui_preferences": user.ui_preferences
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user by ID"""
    # Check permissions
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update user"
        )
    
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(
            user_id=user_id,
            user_data=user_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            full_name_ar=updated_user.full_name_ar,
            full_name_en=updated_user.full_name_en,
            display_name=updated_user.display_name,
            language_preference=updated_user.language_preference,
            timezone=updated_user.timezone,
            role=updated_user.role,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            avatar_url=updated_user.avatar_url,
            bio=updated_user.bio,
            phone_number=updated_user.phone_number,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            last_login=updated_user.last_login
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) vs hard delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user by ID (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    try:
        user_service = UserService(db)
        
        if soft_delete:
            success = await user_service.deactivate_user(user_id)
        else:
            # For hard delete, we would need to implement this in the service
            # For now, just do soft delete
            success = await user_service.deactivate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users"
        )
    
    try:
        user_service = UserService(db)
        success = await user_service.activate_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get updated user
        user = await user_service.get_user_by_id(user_id)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name_ar=user.full_name_ar,
            full_name_en=user.full_name_en,
            display_name=user.display_name,
            language_preference=user.language_preference,
            timezone=user.timezone,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    current_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    try:
        user_service = UserService(db)
        success = await user_service.change_password(
            user_id=current_user.id,
            current_password=current_password,
            new_password=new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )
