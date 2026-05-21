"""add is_adhoc description created_by to daily_task

Revision ID: f55af99b0057
Revises: 001
Create Date: 2026-05-20 23:18:21.710227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f55af99b0057'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('daily_task', sa.Column('is_adhoc', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('daily_task', sa.Column('description', sa.String(length=500), nullable=True))
    op.add_column('daily_task', sa.Column('created_by', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('daily_task', 'created_by')
    op.drop_column('daily_task', 'description')
    op.drop_column('daily_task', 'is_adhoc')
