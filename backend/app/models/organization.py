from sqlalchemy import String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime
import uuid

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"
    
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description_ar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Organization settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="basic")
    max_users: Mapped[int] = mapped_column(default=10)
    max_agents: Mapped[int] = mapped_column(default=5)
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Address
    address_ar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Saudi Arabia")
    
    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    members = relationship("UserOrganization", back_populates="organization")
    agents = relationship("AIAgent", back_populates="organization")
    integrations = relationship("Integration", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name_ar={self.name_ar})>"
    
    @property
    def display_name(self) -> str:
        """Get display name based on language preference"""
        return self.name_ar or self.name_en or f"Organization {self.id}"


class UserOrganization(Base):
    __tablename__ = "user_organizations"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="members")
    
    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, organization_id={self.organization_id}, role={self.role})>"


# Backward-compatible alias for services still importing the old membership model name.
OrganizationMember = UserOrganization
