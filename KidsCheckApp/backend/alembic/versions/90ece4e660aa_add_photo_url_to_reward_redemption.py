"""add photo_url to reward_redemption

Revision ID: 90ece4e660aa
Revises: 4b98efefd491
Create Date: 2026-05-25 19:09:18.784736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90ece4e660aa'
down_revision: Union[str, None] = '4b98efefd491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reward_redemption', sa.Column('photo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('reward_redemption', 'photo_url')
