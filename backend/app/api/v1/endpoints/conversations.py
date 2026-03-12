from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from ....database import get_db
from ....core.auth_dependency import get_current_user
from ....models.user import User
from ....models.organization import UserOrganization
from ....services.conversation_service import ConversationService
from ....schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationDetailResponse, ConversationListResponse,
    MessageCreate, MessageUpdate, MessageResponse, MessageListResponse,
    ConversationSearchRequest, ConversationStats,
    BulkConversationOperation, BulkConversationOperationResponse,
    ChatRequest, ChatResponse, StreamChunk
)
from ....core.exceptions import (
    ConversationNotFoundError, ConversationPermissionError,
    ConversationValidationError, MessageNotFoundError
)
from ....core.tenant_guard import ensure_org_access

router = APIRouter()


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    status: Optional[str] = Query(None, description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    sort_by: str = Query("last_message_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's conversations with filtering and pagination"""
    try:
        search_request = ConversationSearchRequest(
            query=search,
            agent_id=agent_id,
            status=status,
            language=language,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        conversation_service = ConversationService(db)
        return await conversation_service.list_conversations(
            user_id=current_user.id,
            search_request=search_request
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.create_conversation(
            conversation_data=conversation_data,
            user_id=current_user.id
        )
    except ConversationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = Query(False, description="Include conversation messages"),
    message_limit: int = Query(50, ge=1, le=200, description="Maximum messages to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation by ID"""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            include_messages=include_messages,
            message_limit=message_limit
        )
        membership_result = await db.execute(
            select(UserOrganization.organization_id).where(
                UserOrganization.user_id == current_user.id,
                UserOrganization.organization_id == conversation.organization_id,
                UserOrganization.is_active == True
            )
        )
        ensure_org_access(
            conversation.organization_id,
            membership_result.scalar_one_or_none()
        )
        return conversation
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.update_conversation(
            conversation_id=conversation_id,
            conversation_data=conversation_data,
            user_id=current_user.id
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ConversationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (mark as deleted) vs hard delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete conversation"""
    try:
        conversation_service = ConversationService(db)
        await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            soft_delete=soft_delete
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


# Message endpoints
@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add message to conversation"""
    try:
        # Set conversation_id from URL
        message_data.conversation_id = conversation_id
        
        conversation_service = ConversationService(db)
        return await conversation_service.add_message(
            message_data=message_data,
            user_id=current_user.id
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ConversationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for conversation"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.get_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


# Chat endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message and get AI response"""
    try:
        conversation_service = ConversationService(db)
        
        # Create or get conversation
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            # Create new conversation
            conversation_data = ConversationCreate(
                agent_id=chat_request.agent_id,
                language=chat_request.language,
                initial_message=chat_request.message
            )
            conversation = await conversation_service.create_conversation(
                conversation_data=conversation_data,
                user_id=current_user.id
            )
            conversation_id = conversation.id
        
        # Add user message
        user_message_data = MessageCreate(
            content=chat_request.message,
            role="user",
            message_type=chat_request.message_type,
            language=chat_request.language,
            conversation_id=conversation_id,
            attachments=chat_request.attachments
        )
        
        user_message = await conversation_service.add_message(
            message_data=user_message_data,
            user_id=current_user.id
        )
        
        # Generate AI response (placeholder - integrate with AI service)
        ai_response_content = f"This is a placeholder AI response to: {chat_request.message}"
        
        ai_message_data = MessageCreate(
            content=ai_response_content,
            role="assistant",
            message_type="text",
            language=chat_request.language,
            conversation_id=conversation_id
        )
        
        ai_message = await conversation_service.add_message(
            message_data=ai_message_data,
            user_id=current_user.id
        )
        
        # Get updated conversation
        conversation = await conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=ai_message,
            conversation=ConversationResponse.from_orm(conversation)
        )
        
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ConversationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}"
        )


# Statistics endpoint
@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation statistics for current user"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.get_conversation_stats(
            user_id=current_user.id,
            days=days
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation stats: {str(e)}"
        )


# Bulk operations endpoint
@router.post("/bulk", response_model=BulkConversationOperationResponse)
async def bulk_conversation_operation(
    operation_data: BulkConversationOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk operations on conversations"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.bulk_operation(
            operation_data=operation_data,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}"
        )
