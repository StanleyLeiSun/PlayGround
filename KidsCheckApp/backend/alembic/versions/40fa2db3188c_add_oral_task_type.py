"""add_oral_task_type

Revision ID: 40fa2db3188c
Revises: 90ece4e660aa
Create Date: 2026-06-02 15:32:54.181456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40fa2db3188c'
down_revision: Union[str, None] = '90ece4e660aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add oral_image_url columns
    op.add_column('task_template', sa.Column('oral_image_url', sa.String(), nullable=True))
    op.add_column('daily_task', sa.Column('oral_image_url', sa.String(), nullable=True))

    # Create oral_recording table
    op.create_table('oral_recording',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('daily_task_id', sa.Integer(), nullable=False),
    sa.Column('audio_url', sa.String(length=500), nullable=False),
    sa.Column('duration', sa.Float(), nullable=False),
    sa.Column('recorded_by', sa.Integer(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['daily_task_id'], ['daily_task.id'], ),
    sa.ForeignKeyConstraint(['recorded_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oral_recording_id'), 'oral_recording', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_oral_recording_id'), table_name='oral_recording')
    op.drop_table('oral_recording')
    op.drop_column('daily_task', 'oral_image_url')
    op.drop_column('task_template', 'oral_image_url')
