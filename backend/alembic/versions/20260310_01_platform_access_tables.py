"""add platform access tables

Revision ID: 20260310_01
Revises: 
Create Date: 2026-03-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260310_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "external_api_settings" not in inspector.get_table_names():
        op.create_table(
            "external_api_settings",
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("service_name", sa.String(length=120), nullable=False),
            sa.Column("base_url", sa.String(length=500), nullable=False),
            sa.Column("auth_type", sa.String(length=50), nullable=False),
            sa.Column("api_key_secret", sa.Text(), nullable=True),
            sa.Column("default_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("timeout_seconds", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_external_api_settings_id"), "external_api_settings", ["id"], unique=False)
        op.create_index(op.f("ix_external_api_settings_is_active"), "external_api_settings", ["is_active"], unique=False)
        op.create_index(op.f("ix_external_api_settings_is_deleted"), "external_api_settings", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_external_api_settings_organization_id"), "external_api_settings", ["organization_id"], unique=False)
        op.create_index(op.f("ix_external_api_settings_service_name"), "external_api_settings", ["service_name"], unique=False)

    if "platform_api_keys" not in inspector.get_table_names():
        op.create_table(
            "platform_api_keys",
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("customer_name", sa.String(length=255), nullable=False),
            sa.Column("key_prefix", sa.String(length=20), nullable=False),
            sa.Column("key_hash", sa.String(length=128), nullable=False),
            sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_platform_api_keys_customer_name"), "platform_api_keys", ["customer_name"], unique=False)
        op.create_index(op.f("ix_platform_api_keys_id"), "platform_api_keys", ["id"], unique=False)
        op.create_index(op.f("ix_platform_api_keys_is_active"), "platform_api_keys", ["is_active"], unique=False)
        op.create_index(op.f("ix_platform_api_keys_is_deleted"), "platform_api_keys", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_platform_api_keys_key_hash"), "platform_api_keys", ["key_hash"], unique=True)
        op.create_index(op.f("ix_platform_api_keys_key_prefix"), "platform_api_keys", ["key_prefix"], unique=False)
        op.create_index(op.f("ix_platform_api_keys_organization_id"), "platform_api_keys", ["organization_id"], unique=False)

    if "audit_events" not in inspector.get_table_names():
        op.create_table(
            "audit_events",
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("resource_type", sa.String(length=80), nullable=False),
            sa.Column("resource_id", sa.String(length=120), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False)
        op.create_index(op.f("ix_audit_events_id"), "audit_events", ["id"], unique=False)
        op.create_index(op.f("ix_audit_events_is_deleted"), "audit_events", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_audit_events_organization_id"), "audit_events", ["organization_id"], unique=False)
        op.create_index(op.f("ix_audit_events_resource_id"), "audit_events", ["resource_id"], unique=False)
        op.create_index(op.f("ix_audit_events_resource_type"), "audit_events", ["resource_type"], unique=False)
        op.create_index(op.f("ix_audit_events_timestamp"), "audit_events", ["timestamp"], unique=False)
        op.create_index(op.f("ix_audit_events_user_id"), "audit_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_user_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_timestamp"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_resource_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_resource_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_organization_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_is_deleted"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index(op.f("ix_platform_api_keys_organization_id"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_key_prefix"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_key_hash"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_is_deleted"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_is_active"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_id"), table_name="platform_api_keys")
    op.drop_index(op.f("ix_platform_api_keys_customer_name"), table_name="platform_api_keys")
    op.drop_table("platform_api_keys")

    op.drop_index(op.f("ix_external_api_settings_service_name"), table_name="external_api_settings")
    op.drop_index(op.f("ix_external_api_settings_organization_id"), table_name="external_api_settings")
    op.drop_index(op.f("ix_external_api_settings_is_deleted"), table_name="external_api_settings")
    op.drop_index(op.f("ix_external_api_settings_is_active"), table_name="external_api_settings")
    op.drop_index(op.f("ix_external_api_settings_id"), table_name="external_api_settings")
    op.drop_table("external_api_settings")
