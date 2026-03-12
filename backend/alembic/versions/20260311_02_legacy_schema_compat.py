"""legacy schema compatibility for v1 models

Revision ID: 20260311_02
Revises: 20260310_01
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260311_02"
down_revision: Union[str, Sequence[str], None] = "20260310_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if not _has_column(inspector, table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names())
    if "organizations" in table_names:
        _add_column_if_missing(inspector, "organizations", sa.Column("description_ar", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("description_en", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("subscription_plan", sa.String(length=50), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("max_agents", sa.Integer(), nullable=False, server_default="5"))
        _add_column_if_missing(inspector, "organizations", sa.Column("email", sa.String(length=255), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("phone", sa.String(length=20), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("website", sa.String(length=500), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("address_ar", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("address_en", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("city", sa.String(length=100), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("country", sa.String(length=100), nullable=False, server_default="Saudi Arabia"))
        _add_column_if_missing(inspector, "organizations", sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "organizations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "organizations", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

        if _has_column(inspector, "organizations", "subscription_tier"):
            op.execute(
                sa.text(
                    """
                    UPDATE organizations
                    SET subscription_plan = COALESCE(subscription_plan, subscription_tier)
                    WHERE subscription_plan IS NULL
                    """
                )
            )
        op.execute(sa.text("UPDATE organizations SET subscription_plan = 'basic' WHERE subscription_plan IS NULL"))
        op.alter_column("organizations", "subscription_plan", existing_type=sa.String(length=50), nullable=False, server_default="basic")

    if "user_organizations" in table_names:
        _add_column_if_missing(inspector, "user_organizations", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "user_organizations", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    if "ai_agents" in table_names:
        _add_column_if_missing(inspector, "ai_agents", sa.Column("status", sa.String(length=50), nullable=False, server_default="active"))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("llm_provider", sa.String(length=50), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("llm_model", sa.String(length=100), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("system_prompt_ar", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("system_prompt_en", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("max_tokens", sa.String(length=10), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("temperature", sa.String(length=5), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("prompt_templates", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("response_templates", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("api_endpoints", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("allowed_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0.0"))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "ai_agents", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(sa.text("UPDATE ai_agents SET status='active' WHERE status IS NULL"))
        op.execute(sa.text("UPDATE ai_agents SET llm_provider='anthropic' WHERE llm_provider IS NULL"))
        op.execute(sa.text("UPDATE ai_agents SET llm_model='claude-3-sonnet' WHERE llm_model IS NULL"))
        op.execute(sa.text("UPDATE ai_agents SET max_tokens='4000' WHERE max_tokens IS NULL"))
        op.execute(sa.text("UPDATE ai_agents SET temperature='0.7' WHERE temperature IS NULL"))

    if "enterprise_integrations" in table_names:
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("description", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("sync_status", sa.String(length=50), nullable=True, server_default="pending"))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("sync_error", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("health_check_url", sa.String(length=500), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("health_status", sa.String(length=20), nullable=True, server_default="unknown"))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "enterprise_integrations", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    if "conversations" in table_names:
        _add_column_if_missing(inspector, "conversations", sa.Column("title", sa.String(length=255), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("summary", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("language", sa.String(length=10), nullable=False, server_default="ar"))
        _add_column_if_missing(inspector, "conversations", sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing(inspector, "conversations", sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("conversation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
        _add_column_if_missing(inspector, "conversations", sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "conversations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "conversations", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        if _has_column(inspector, "conversations", "title_en"):
            op.execute(sa.text("UPDATE conversations SET title = COALESCE(title, title_en, title_ar)"))

    if "messages" in table_names:
        _add_column_if_missing(inspector, "messages", sa.Column("content", sa.Text(), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("role", sa.String(length=20), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("message_type", sa.String(length=20), nullable=False, server_default="text"))
        _add_column_if_missing(inspector, "messages", sa.Column("language", sa.String(length=10), nullable=False, server_default="ar"))
        _add_column_if_missing(inspector, "messages", sa.Column("tokens_used", sa.Integer(), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("processing_time", sa.Float(), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
        _add_column_if_missing(inspector, "messages", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "messages", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
        _add_column_if_missing(inspector, "messages", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        if _has_column(inspector, "messages", "content_en"):
            op.execute(sa.text("UPDATE messages SET content = COALESCE(content, content_en, content_ar)"))
        if _has_column(inspector, "messages", "sender_type"):
            op.execute(sa.text("UPDATE messages SET role = COALESCE(role, sender_type)"))
        if _has_column(inspector, "messages", "metadata"):
            op.execute(sa.text("UPDATE messages SET message_metadata = COALESCE(message_metadata, metadata)"))
        op.execute(sa.text("UPDATE messages SET content = COALESCE(content, '') WHERE content IS NULL"))
        op.execute(sa.text("UPDATE messages SET role = COALESCE(role, 'user') WHERE role IS NULL"))
        op.alter_column("messages", "content", existing_type=sa.Text(), nullable=False)
        op.alter_column("messages", "role", existing_type=sa.String(length=20), nullable=False)


def downgrade() -> None:
    # Compatibility migration is intentionally non-destructive.
    pass
