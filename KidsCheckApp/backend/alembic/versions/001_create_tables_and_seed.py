"""Create all tables and seed data

Revision ID: 001
Revises:
Create Date: 2026-05-18

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tables
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("parent", "grandparent", name="userrole"), nullable=False),
    )

    op.create_table(
        "child",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
    )

    op.create_table(
        "task_template",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("type", sa.Enum("written", "reading", name="tasktype"), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_task_template_child_weekday", "task_template", ["child_id", "weekday"])

    op.create_table(
        "conditional_task",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), nullable=False),
        sa.Column("trigger_condition", sa.String(50), nullable=False, server_default="all_required_done"),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("type", sa.Enum("written", "reading", name="tasktype"), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False, server_default="5"),
    )

    op.create_table(
        "daily_task",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("source_template_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("type", sa.Enum("written", "reading", name="tasktype"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.Enum("pending", "done", name="taskstatus"), nullable=False, server_default="pending"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("is_conditional", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_daily_task_child_date", "daily_task", ["child_id", "date"])

    op.create_table(
        "check_in_photo",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("daily_task_id", sa.Integer(), sa.ForeignKey("daily_task.id"), nullable=False),
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("review_note", sa.String(255), nullable=True),
    )

    op.create_table(
        "point_account",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), unique=True, nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "point_transaction",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("related_task_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_point_transaction_child_created", "point_transaction", ["child_id", "created_at"])

    op.create_table(
        "reward",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("cost_points", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
    )

    op.create_table(
        "reward_redemption",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("child.id"), nullable=False),
        sa.Column("reward_id", sa.Integer(), sa.ForeignKey("reward.id"), nullable=False),
        sa.Column("points_spent", sa.Integer(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum("pending", "fulfilled", name="redemptionstatus"), nullable=False, server_default="pending"),
    )

    op.create_table(
        "action_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_action_log_user_created", "action_log", ["user_id", "created_at"])

    # Seed data: 6 users (password depends on environment)
    env = os.getenv("APP_ENV", "dev")
    password = "123456" if env == "dev" else "KidsCheck2026!"

    op.execute(f"""
        INSERT INTO "user" (username, password_hash, role) VALUES
        ('爸爸', '{password}', 'parent'),
        ('妈妈', '{password}', 'parent'),
        ('爷爷', '{password}', 'grandparent'),
        ('奶奶', '{password}', 'grandparent'),
        ('姥姥', '{password}', 'grandparent'),
        ('姥爷', '{password}', 'grandparent')
    """)

    # Seed data: 2 children
    op.execute("""
        INSERT INTO child (name, nickname, age) VALUES
        ('孙北峤', '萝卜', 8),
        ('孙南崧', '蚕豆', 5)
    """)

    # Seed data: 2 point accounts
    op.execute("""
        INSERT INTO point_account (child_id, balance) VALUES
        (1, 0), (2, 0)
    """)


def downgrade() -> None:
    op.drop_table("action_log")
    op.drop_table("reward_redemption")
    op.drop_table("reward")
    op.drop_table("point_transaction")
    op.drop_table("point_account")
    op.drop_table("check_in_photo")
    op.drop_table("daily_task")
    op.drop_table("conditional_task")
    op.drop_table("task_template")
    op.drop_table("child")
    op.drop_table("user")
