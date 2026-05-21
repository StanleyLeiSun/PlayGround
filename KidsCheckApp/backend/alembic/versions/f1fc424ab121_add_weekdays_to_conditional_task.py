"""add weekdays to conditional_task

Revision ID: f1fc424ab121
Revises: f55af99b0057
Create Date: 2026-05-21 23:25:22.783009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1fc424ab121'
down_revision: Union[str, None] = 'f55af99b0057'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conditional_task', sa.Column('weekdays', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('conditional_task', 'weekdays')
