import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey, DateTime, Boolean, Text, Float,
    Index, UniqueConstraint, JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    parent = "parent"
    grandparent = "grandparent"


class TaskType(str, enum.Enum):
    written = "written"
    reading = "reading"
    oral = "oral"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    done = "done"


class RedemptionStatus(str, enum.Enum):
    pending = "pending"
    fulfilled = "fulfilled"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    wechat_openid = Column(String(128), unique=True, nullable=True)


class Child(Base):
    __tablename__ = "child"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    nickname = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)

    task_templates = relationship("TaskTemplate", back_populates="child", lazy="selectin")
    conditional_tasks = relationship("ConditionalTask", back_populates="child", lazy="selectin")
    daily_tasks = relationship("DailyTask", back_populates="child", lazy="selectin")
    point_account = relationship("PointAccount", back_populates="child", uselist=False, lazy="selectin")


class TaskTemplate(Base):
    __tablename__ = "task_template"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    title = Column(String(100), nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    description = Column(String(255), nullable=True)
    points = Column(Integer, nullable=False, default=5)
    sort_order = Column(Integer, nullable=False, default=0)
    oral_image_url = Column(String, nullable=True)

    child = relationship("Child", back_populates="task_templates")

    __table_args__ = (
        Index("ix_task_template_child_weekday", "child_id", "weekday"),
    )


class ConditionalTask(Base):
    __tablename__ = "conditional_task"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)
    trigger_condition = Column(String(50), nullable=False, default="all_required_done")
    title = Column(String(100), nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    description = Column(String(255), nullable=True)
    points = Column(Integer, nullable=False, default=5)
    weekdays = Column(String(50), nullable=True)

    child = relationship("Child", back_populates="conditional_tasks")


class DailyTask(Base):
    __tablename__ = "daily_task"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    source_template_id = Column(Integer, nullable=True)  # FK to task_template or conditional_task
    title = Column(String(100), nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    points = Column(Integer, nullable=False, default=5)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    is_conditional = Column(Boolean, nullable=False, default=False)
    is_adhoc = Column(Boolean, nullable=False, default=False)
    description = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    oral_image_url = Column(String, nullable=True)

    child = relationship("Child", back_populates="daily_tasks")
    photos = relationship("CheckInPhoto", back_populates="daily_task", lazy="selectin")
    recordings = relationship("OralRecording", back_populates="daily_task", lazy="selectin")

    __table_args__ = (
        Index("ix_daily_task_child_date", "child_id", "date"),
    )


class CheckInPhoto(Base):
    __tablename__ = "check_in_photo"

    id = Column(Integer, primary_key=True, index=True)
    daily_task_id = Column(Integer, ForeignKey("daily_task.id"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed = Column(Boolean, nullable=False, default=False)
    review_note = Column(String(255), nullable=True)

    daily_task = relationship("DailyTask", back_populates="photos")


class OralRecording(Base):
    __tablename__ = "oral_recording"

    id = Column(Integer, primary_key=True, index=True)
    daily_task_id = Column(Integer, ForeignKey("daily_task.id"), nullable=False)
    audio_url = Column(String(500), nullable=False)
    duration = Column(Float, nullable=False)  # seconds
    recorded_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    daily_task = relationship("DailyTask", back_populates="recordings")


class PointAccount(Base):
    __tablename__ = "point_account"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), unique=True, nullable=False)
    balance = Column(Integer, nullable=False, default=0)

    child = relationship("Child", back_populates="point_account")


class PointTransaction(Base):
    __tablename__ = "point_transaction"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    related_task_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_point_transaction_child_created", "child_id", "created_at"),
    )


class Reward(Base):
    __tablename__ = "reward"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    cost_points = Column(Integer, nullable=False)
    description = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)


class RewardRedemption(Base):
    __tablename__ = "reward_redemption"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("child.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("reward.id"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    redeemed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(Enum(RedemptionStatus), nullable=False, default=RedemptionStatus.pending)
    photo_url = Column(String(500), nullable=True)


class ActionLog(Base):
    __tablename__ = "action_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    meta = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_action_log_user_created", "user_id", "created_at"),
    )
