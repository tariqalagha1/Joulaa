import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ....database import get_db
from ....models.agent import AgentType, AgentStatus, AgentCapability
from ....schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentDetailResponse,
    AgentListResponse, AgentTemplateResponse, AgentChatRequest,
    AgentChatResponse, BulkAgentOperation, BulkAgentOperationResponse
)
from ....services.agent_service import AgentService
from ....services.ai_service import ai_service
from ....core.auth import get_current_organization
from ....core.auth_dependency import get_current_user
from ....core.feature_flags import is_feature_enabled, FeatureFlag
from ....core.exceptions import (
    AgentNotFoundError, FeatureNotEnabledError, ValidationError
)
from ....core.audit import log_audit_event
from ....models.user import User
from ....core.tenant_guard import ensure_org_access

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Create a new AI agent"""
    if not is_feature_enabled(FeatureFlag.AGENT_STUDIO):
        raise FeatureNotEnabledError("AI Agent Studio")
    
    try:
        agent_service = AgentService(db)
        agent = await agent_service.create_agent(
            agent_data=agent_data,
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        logger.info(
            "Agent created via API",
            agent_id=agent.id,
            agent_name=agent.name_ar or agent.name_en,
            created_by=current_user.id
        )
        log_audit_event(
            event_type="agent.create",
            user_id=current_user.id,
            organization_id=organization_id,
            resource_type="agent",
            resource_id=agent.id,
            metadata={"agent_type": str(agent.agent_type)},
        )
        
        return agent
        
    except Exception as e:
        logger.error(
            "Failed to create agent via API",
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    status: Optional[AgentStatus] = Query(None, description="Filter by agent status"),
    capabilities: Optional[List[AgentCapability]] = Query(None, description="Filter by capabilities"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_id: UUID = Depends(get_current_organization)
):
    """List AI agents with filtering and pagination"""
    try:
        agent_service = AgentService(db)
        agents = await agent_service.list_agents(
            user_id=current_user.id,
            organization_id=organization_id,
            agent_type=agent_type,
            status=status,
            capabilities=capabilities,
            search=search,
            page=page,
            page_size=page_size
        )
        
        return agents
        
    except Exception as e:
        logger.error(
            "Failed to list agents via API",
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: UUID,
    include_metrics: bool = Query(False, description="Include agent metrics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Get agent by ID with detailed information"""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            organization_id=organization_id,
            include_metrics=include_metrics
        )
        ensure_org_access(getattr(agent, "organization_id", None), organization_id)
        
        return agent
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get agent via API",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get agent")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Update an existing agent"""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.update_agent(
            agent_id=agent_id,
            agent_data=agent_data,
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        logger.info(
            "Agent updated via API",
            agent_id=agent_id,
            updated_by=current_user.id
        )
        
        return agent
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update agent via API",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: UUID,
    force: bool = Query(False, description="Force delete even with active conversations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Delete an agent"""
    try:
        agent_service = AgentService(db)
        success = await agent_service.delete_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            organization_id=organization_id,
            force=force
        )
        
        logger.info(
            "Agent deleted via API",
            agent_id=agent_id,
            deleted_by=current_user.id,
            force_delete=force
        )
        log_audit_event(
            event_type="agent.delete",
            user_id=current_user.id,
            organization_id=organization_id,
            resource_type="agent",
            resource_id=agent_id,
            metadata={"force_delete": force},
        )
        
        return {"message": "Agent deleted successfully", "success": success}
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to delete agent via API",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete agent")


@router.post("/bulk", response_model=BulkAgentOperationResponse)
async def bulk_agent_operation(
    operation: BulkAgentOperation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Perform bulk operations on agents"""
    bulk_flag = getattr(FeatureFlag, "BULK_OPERATIONS", None)
    if bulk_flag is not None and not is_feature_enabled(bulk_flag):
        raise FeatureNotEnabledError("Bulk Operations")
    
    try:
        agent_service = AgentService(db)
        result = await agent_service.bulk_operation(
            operation=operation,
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        logger.info(
            "Bulk agent operation completed",
            operation=operation.operation,
            total_agents=len(operation.agent_ids),
            successful=result.successful,
            failed=result.failed,
            performed_by=current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Failed to perform bulk agent operation",
            operation=operation.operation,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to perform bulk operation")


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: UUID,
    chat_request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Chat with an AI agent"""
    if not is_feature_enabled(FeatureFlag.AI_CHAT):
        raise FeatureNotEnabledError("AI Chat")
    
    try:
        # Get agent
        agent_service = AgentService(db)
        agent_detail = await agent_service.get_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        # Convert to AI agent model (simplified for this example)
        from ....models.agent import AIAgent
        agent = AIAgent(
            id=agent_detail.id,
            name=agent_detail.name,
            agent_type=agent_detail.agent_type,
            llm_provider=agent_detail.llm_provider,
            llm_model=agent_detail.llm_model,
            system_prompt_ar=agent_detail.system_prompt_ar,
            system_prompt_en=agent_detail.system_prompt_en,
            temperature=agent_detail.temperature,
            max_tokens=agent_detail.max_tokens
        )
        
        # Chat with agent
        response = await ai_service.chat_with_agent(
            agent=agent,
            request=chat_request
        )
        
        logger.info(
            "Agent chat completed",
            agent_id=agent_id,
            user_id=current_user.id,
            response_time=response.response_time,
            tokens_used=response.tokens_used
        )
        
        return response
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to chat with agent",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to chat with agent")


@router.post("/{agent_id}/chat/stream")
async def stream_chat_with_agent(
    agent_id: UUID,
    chat_request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Stream chat with an AI agent"""
    if not is_feature_enabled(FeatureFlag.AI_CHAT) or not is_feature_enabled(FeatureFlag.STREAMING_RESPONSES):
        raise FeatureNotEnabledError("AI Chat Streaming")
    
    try:
        # Get agent
        agent_service = AgentService(db)
        agent_detail = await agent_service.get_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        # Convert to AI agent model
        from ....models.agent import AIAgent
        agent = AIAgent(
            id=agent_detail.id,
            name=agent_detail.name,
            agent_type=agent_detail.agent_type,
            llm_provider=agent_detail.llm_provider,
            llm_model=agent_detail.llm_model,
            system_prompt_ar=agent_detail.system_prompt_ar,
            system_prompt_en=agent_detail.system_prompt_en,
            temperature=agent_detail.temperature,
            max_tokens=agent_detail.max_tokens
        )
        
        async def generate_stream():
            try:
                async for chunk in ai_service.stream_chat_with_agent(
                    agent=agent,
                    request=chat_request
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(
                    "Error in chat stream",
                    agent_id=agent_id,
                    error=str(e),
                    exc_info=True
                )
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to start chat stream",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to start chat stream")


@router.get("/templates/", response_model=List[AgentTemplateResponse])
async def get_agent_templates(
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    language: str = Query("ar", description="Template language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Get available agent templates"""
    if not is_feature_enabled(FeatureFlag.AGENT_TEMPLATES):
        raise FeatureNotEnabledError("Agent Templates")
    
    try:
        agent_service = AgentService(db)
        templates = await agent_service.get_agent_templates(
            organization_id=organization_id,
            agent_type=agent_type,
            language=language
        )
        
        return templates
        
    except Exception as e:
        logger.error(
            "Failed to get agent templates",
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get agent templates")


@router.post("/templates/{template_id}/create", response_model=AgentResponse)
async def create_agent_from_template(
    template_id: UUID,
    agent_name: str = Query(..., description="Name for the new agent"),
    customizations: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Create an agent from a template"""
    if not is_feature_enabled(FeatureFlag.AGENT_TEMPLATES):
        raise FeatureNotEnabledError("Agent Templates")
    
    try:
        agent_service = AgentService(db)
        agent = await agent_service.create_agent_from_template(
            template_id=template_id,
            agent_name=agent_name,
            user_id=current_user.id,
            organization_id=organization_id,
            customizations=customizations
        )
        
        logger.info(
            "Agent created from template",
            template_id=template_id,
            agent_id=agent.id,
            agent_name=agent_name,
            created_by=current_user.id
        )
        
        return agent
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create agent from template",
            template_id=template_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create agent from template")


@router.get("/{agent_id}/metrics", response_model=Dict[str, Any])
async def get_agent_metrics(
    agent_id: UUID,
    period: str = Query("7d", description="Metrics period (1d, 7d, 30d, 90d)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_organization)
):
    """Get detailed agent metrics and analytics"""
    if not is_feature_enabled(FeatureFlag.ANALYTICS):
        raise FeatureNotEnabledError("Analytics")
    
    try:
        # This would implement detailed metrics collection
        # For now, return placeholder data
        metrics = {
            "agent_id": agent_id,
            "period": period,
            "total_conversations": 150,
            "total_messages": 1250,
            "average_response_time": 1.2,
            "success_rate": 0.95,
            "user_satisfaction": 4.3,
            "popular_topics": [
                {"topic": "Financial Reports", "count": 45},
                {"topic": "Budget Analysis", "count": 32},
                {"topic": "Expense Tracking", "count": 28}
            ],
            "usage_by_hour": [
                {"hour": 9, "count": 25},
                {"hour": 10, "count": 35},
                {"hour": 11, "count": 40},
                {"hour": 14, "count": 30},
                {"hour": 15, "count": 20}
            ]
        }
        
        return metrics
        
    except Exception as e:
        logger.error(
            "Failed to get agent metrics",
            agent_id=agent_id,
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get agent metrics")
