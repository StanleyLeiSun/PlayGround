"""add wechat_openid to user

Revision ID: 4b98efefd491
Revises: f1fc424ab121
Create Date: 2026-05-22 17:47:58.279862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b98efefd491'
down_revision: Union[str, None] = 'f1fc424ab121'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('wechat_openid', sa.String(length=128), nullable=True))
    with op.batch_alter_table('user') as batch_op:
        batch_op.create_unique_constraint('uq_user_wechat_openid', ['wechat_openid'])


def downgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_constraint('uq_user_wechat_openid', type_='unique')
    op.drop_column('user', 'wechat_openid')
