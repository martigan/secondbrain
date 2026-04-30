"""Add composite index for task pagination

Revision ID: 0002_tasks_pagination_index
Revises: 0001_initial
Create Date: 2026-04-29 11:05:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_tasks_pagination_index"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_user_created_at_id_desc",
        "tasks",
        ["created_by_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_created_at_id_desc", table_name="tasks")
