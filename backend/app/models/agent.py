from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from typing import Dict, Any, Optional, List

from ..database import Base


class AgentType(str, enum.Enum):
    """Types of AI agents available in the platform"""
    FINANCE = "finance"
    PROCUREMENT = "procurement"
    HR = "hr"
    SUPPLY_CHAIN = "supply_chain"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class AgentStatus(str, enum.Enum):
    """Status of an AI agent"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class AgentCapability(str, enum.Enum):
    """Capabilities that agents can have"""
    # Data Analysis
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    TREND_ANALYSIS = "trend_analysis"
    
    # Communication
    CHAT_SUPPORT = "chat_support"
    EMAIL_AUTOMATION = "email_automation"
    NOTIFICATION_MANAGEMENT = "notification_management"
    
    # Integration
    API_INTEGRATION = "api_integration"
    DATABASE_QUERY = "database_query"
    FILE_PROCESSING = "file_processing"
    
    # Workflow
    TASK_AUTOMATION = "task_automation"
    APPROVAL_WORKFLOWS = "approval_workflows"
    SCHEDULING = "scheduling"
    
    # AI/ML
    NATURAL_LANGUAGE_PROCESSING = "nlp"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    
    # Arabic-specific
    ARABIC_TEXT_PROCESSING = "arabic_text_processing"
    RTL_DOCUMENT_HANDLING = "rtl_document_handling"
    ARABIC_SPEECH_RECOGNITION = "arabic_speech_recognition"


class AIAgent(Base):
    """AI Agent model for storing agent configurations"""
    
    __tablename__ = "ai_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Information
    name_ar = Column(String(255), nullable=False, comment="Agent name in Arabic")
    name_en = Column(String(255), nullable=True, comment="Agent name in English")
    description_ar = Column(Text, nullable=True, comment="Agent description in Arabic")
    description_en = Column(Text, nullable=True, comment="Agent description in English")
    
    # Agent Configuration
    # Keep as String for compatibility with legacy DB schemas that don't have PG enum types.
    agent_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default=AgentStatus.ACTIVE.value, index=True)
    capabilities = Column(JSONB, nullable=False, default=list, comment="List of agent capabilities")
    
    # AI Configuration
    llm_provider = Column(String(50), default="anthropic", comment="LLM provider (openai, anthropic, etc.)")
    llm_model = Column(String(100), default="claude-3-sonnet", comment="Specific model to use")
    system_prompt_ar = Column(Text, nullable=True, comment="System prompt in Arabic")
    system_prompt_en = Column(Text, nullable=True, comment="System prompt in English")
    max_tokens = Column(String(10), default="4000", comment="Maximum tokens per response")
    temperature = Column(String(5), default="0.7", comment="LLM temperature setting")
    
    # Behavior Configuration
    configuration = Column(JSONB, nullable=False, default=dict, comment="Agent-specific configuration")
    prompt_templates = Column(JSONB, nullable=False, default=dict, comment="Prompt templates for different scenarios")
    response_templates = Column(JSONB, nullable=False, default=dict, comment="Response templates")
    
    # Integration Settings
    integrations = Column(JSONB, nullable=False, default=list, comment="Connected enterprise systems")
    api_endpoints = Column(JSONB, nullable=False, default=dict, comment="API endpoints the agent can access")
    
    # Permissions and Access
    permissions = Column(JSONB, nullable=False, default=dict, comment="Agent permissions and access levels")
    allowed_actions = Column(JSONB, nullable=False, default=list, comment="Actions the agent can perform")
    
    # Metadata
    version = Column(String(20), default="1.0.0", comment="Agent version")
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False, comment="Whether agent is available to all organizations")
    
    # Relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="agents")
    creator = relationship("User", foreign_keys=[created_by])
    conversations = relationship("Conversation", back_populates="agent")
    agent_metrics = relationship("AgentMetrics", back_populates="agent")
    
    def __repr__(self):
        return f"<AIAgent(id={self.id}, name_ar='{self.name_ar}', type={self.agent_type})>"
    
    @property
    def display_name(self) -> str:
        """Get display name based on current language context"""
        # This would be determined by request context in a real app
        return self.name_ar or self.name_en or f"Agent {self.id}"
    
    def get_capability_list(self) -> List[AgentCapability]:
        """Get list of agent capabilities as enum values"""
        if not self.capabilities:
            return []
        return [AgentCapability(cap) for cap in self.capabilities if cap in AgentCapability.__members__.values()]
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability"""
        return capability.value in (self.capabilities or [])
    
    def get_integration_config(self, integration_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific integration"""
        if not self.integrations:
            return None
        
        for integration in self.integrations:
            if integration.get("type") == integration_type:
                return integration
        return None
    
    def is_accessible_by_user(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        """Check if agent is accessible by a specific user"""
        if self.is_public:
            return True
        
        if self.organization_id == organization_id:
            return True
        
        if self.created_by == user_id:
            return True
        
        return False


class AgentMetrics(Base):
    """Metrics and analytics for AI agents"""
    
    __tablename__ = "agent_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False)
    
    # Usage Metrics
    total_conversations = Column(String(20), default="0")
    total_messages = Column(String(20), default="0")
    total_tokens_used = Column(String(20), default="0")
    average_response_time = Column(String(10), default="0.0", comment="Average response time in seconds")
    
    # Performance Metrics
    success_rate = Column(String(5), default="0.0", comment="Success rate percentage")
    user_satisfaction_score = Column(String(5), default="0.0", comment="Average user satisfaction (1-5)")
    error_rate = Column(String(5), default="0.0", comment="Error rate percentage")
    
    # Time-based Metrics
    metrics_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily", comment="daily, weekly, monthly")
    
    # Detailed Metrics
    metrics_data = Column(JSONB, nullable=False, default=dict, comment="Detailed metrics data")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("AIAgent", back_populates="agent_metrics")
    
    def __repr__(self):
        return f"<AgentMetrics(agent_id={self.agent_id}, date={self.metrics_date})>"


class AgentTemplate(Base):
    """Pre-built agent templates for quick setup"""
    
    __tablename__ = "agent_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template Information
    name_ar = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    
    # Template Configuration
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    template_config = Column(JSONB, nullable=False, comment="Complete agent configuration template")
    
    # Template Metadata
    category = Column(String(100), nullable=True, comment="Template category")
    tags = Column(JSONB, nullable=False, default=list, comment="Template tags for search")
    difficulty_level = Column(String(20), default="beginner", comment="beginner, intermediate, advanced")
    
    # Usage and Popularity
    usage_count = Column(String(20), default="0", comment="Number of times template was used")
    rating = Column(String(5), default="0.0", comment="Average user rating")
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    requires_premium = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AgentTemplate(id={self.id}, name_ar='{self.name_ar}', type={self.agent_type})>"


class AgentWorkflow(Base):
    """Workflow definitions for agents"""
    
    __tablename__ = "agent_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False)
    
    # Workflow Information
    name_ar = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    
    # Workflow Configuration
    workflow_steps = Column(JSONB, nullable=False, comment="Ordered list of workflow steps")
    triggers = Column(JSONB, nullable=False, default=list, comment="Workflow triggers")
    conditions = Column(JSONB, nullable=False, default=dict, comment="Workflow execution conditions")
    
    # Execution Settings
    is_active = Column(Boolean, default=True)
    auto_execute = Column(Boolean, default=False, comment="Whether workflow executes automatically")
    max_execution_time = Column(String(10), default="300", comment="Maximum execution time in seconds")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("AIAgent")
    
    def __repr__(self):
        return f"<AgentWorkflow(id={self.id}, agent_id={self.agent_id}, name_ar='{self.name_ar}')>"
