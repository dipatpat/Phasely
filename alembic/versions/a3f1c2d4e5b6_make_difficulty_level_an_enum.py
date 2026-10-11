"""Make training_plan_exercise.difficulty_level an enum

Revision ID: a3f1c2d4e5b6
Revises: 56d7a478f3de
Create Date: 2026-10-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f1c2d4e5b6"
down_revision: str | Sequence[str] | None = "56d7a478f3de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

difficulty_level_enum = sa.Enum("easy", "medium", "hard", name="difficultylevel")


def upgrade() -> None:
    """Upgrade schema."""
    difficulty_level_enum.create(op.get_bind(), checkfirst=True)
    # Existing free-text values are normalised; anything unrecognised becomes NULL
    op.alter_column(
        "training_plan_exercise",
        "difficulty_level",
        existing_type=sa.String(length=50),
        type_=difficulty_level_enum,
        existing_nullable=True,
        postgresql_using=(
            "CASE WHEN lower(trim(difficulty_level)) IN ('easy', 'medium', 'hard') "
            "THEN lower(trim(difficulty_level))::difficultylevel "
            "ELSE NULL END"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "training_plan_exercise",
        "difficulty_level",
        existing_type=difficulty_level_enum,
        type_=sa.String(length=50),
        existing_nullable=True,
        postgresql_using="difficulty_level::text",
    )
    difficulty_level_enum.drop(op.get_bind(), checkfirst=True)
