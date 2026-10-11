"""Add partial unique index preventing double-booked sessions

Revision ID: b7e2d9f0c1a4
Revises: a3f1c2d4e5b6
Create Date: 2026-10-11 13:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e2d9f0c1a4"
down_revision: str | Sequence[str] | None = "a3f1c2d4e5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_session_trainer_scheduled_active",
        "session",
        ["trainer_id", "scheduled_at"],
        unique=True,
        postgresql_where="status != 'cancelled'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_session_trainer_scheduled_active",
        table_name="session",
        postgresql_where="status != 'cancelled'",
    )
