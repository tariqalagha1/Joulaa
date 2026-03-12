"""allow nullable sender_type for legacy messages schema

Revision ID: 20260311_03
Revises: 20260311_02
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260311_03"
down_revision: Union[str, Sequence[str], None] = "20260311_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "messages" not in tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns("messages")}
    if "sender_type" in columns and not columns["sender_type"].get("nullable", True):
        op.alter_column(
            "messages",
            "sender_type",
            existing_type=sa.String(length=20),
            nullable=True,
        )


def downgrade() -> None:
    # Non-destructive compatibility migration.
    pass

