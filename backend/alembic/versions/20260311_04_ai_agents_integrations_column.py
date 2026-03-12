"""add missing ai_agents.integrations column

Revision ID: 20260311_04
Revises: 20260311_03
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260311_04"
down_revision: Union[str, Sequence[str], None] = "20260311_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ai_agents" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("ai_agents")}
    if "integrations" not in columns:
        op.add_column(
            "ai_agents",
            sa.Column(
                "integrations",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )


def downgrade() -> None:
    # Non-destructive compatibility migration.
    pass

