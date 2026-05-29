from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class WechatLoginRequest(BaseModel):
    code: str

class WechatBindRequest(BaseModel):
    openid: str
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


# Child
class ChildResponse(BaseModel):
    id: int
    name: str
    nickname: str
    age: int


# Task Template
class TaskTemplateCreate(BaseModel):
    weekday: int  # 1-7
    title: str
    type: str  # "written" or "reading"
    description: Optional[str] = None
    points: int = 5
    sort_order: int = 0


class TaskTemplateBatchCreate(BaseModel):
    weekdays: list[int]  # e.g. [1, 2, 3]
    title: str
    type: str  # "written" or "reading"
    description: Optional[str] = None
    points: int = 5
    sort_order: int = 0


class TaskTemplateUpdate(BaseModel):
    weekday: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    points: Optional[int] = None
    sort_order: Optional[int] = None


class TaskTemplateResponse(BaseModel):
    id: int
    child_id: int
    weekday: int
    title: str
    type: str
    description: Optional[str]
    points: int
    sort_order: int


class TemplatesByWeekday(BaseModel):
    weekday: int
    weekday_name: str
    templates: list[TaskTemplateResponse]


# Conditional Task
class ConditionalTaskCreate(BaseModel):
    title: str
    type: str  # "written" or "reading"
    description: Optional[str] = None
    points: int = 5
    weekdays: Optional[str] = None


class ConditionalTaskUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    points: Optional[int] = None
    weekdays: Optional[str] = None


class ConditionalTaskResponse(BaseModel):
    id: int
    child_id: int
    trigger_condition: str
    title: str
    type: str
    description: Optional[str]
    points: int
    weekdays: Optional[str] = None


# Daily Task
class AdhocTaskCreate(BaseModel):
    title: str
    type: str = "reading"  # "written" or "reading"
    description: Optional[str] = None
    points: int = 5


class DailyTaskResponse(BaseModel):
    id: int
    child_id: int
    date: datetime
    title: str
    type: str
    points: int
    status: str
    completed_at: Optional[datetime]
    completed_by: Optional[int]
    completed_by_username: Optional[str] = None
    is_conditional: bool
    is_adhoc: bool = False
    description: Optional[str] = None
    photos: list["CheckInPhotoResponse"] = []


class CheckInRequest(BaseModel):
    pass  # Photo is uploaded as multipart


class CheckInPhotoResponse(BaseModel):
    id: int
    photo_url: str
    uploaded_by: int
    uploaded_at: datetime
    reviewed: bool
    review_note: Optional[str]


# Progress
class ProgressResponse(BaseModel):
    child_id: int
    date: datetime
    total_tasks: int
    completed_tasks: int
    today_points: int
    cumulative_points: int
    tasks: list[DailyTaskResponse]


class PhotoReviewRequest(BaseModel):
    reviewed: bool = True
    review_note: Optional[str] = None


# Points
class PointTransactionResponse(BaseModel):
    id: int
    child_id: int
    amount: int
    reason: str
    related_task_id: Optional[int]
    created_at: datetime


class PointBalanceResponse(BaseModel):
    child_id: int
    balance: int
    transactions: list[PointTransactionResponse]


# Reward
class RewardCreate(BaseModel):
    title: str
    cost_points: int
    description: Optional[str] = None
    image_url: Optional[str] = None


class RewardUpdate(BaseModel):
    title: Optional[str] = None
    cost_points: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class RewardResponse(BaseModel):
    id: int
    title: str
    cost_points: int
    description: Optional[str]
    image_url: Optional[str]


class RewardRedemptionResponse(BaseModel):
    id: int
    child_id: int
    child_name: Optional[str] = None
    reward_id: int
    reward_title: Optional[str] = None
    points_spent: int
    redeemed_at: datetime
    status: str
    photo_url: Optional[str] = None


# Voice
class VoiceRequest(BaseModel):
    text: str


class VoiceParsedIntent(BaseModel):
    action: str  # "create", "delete", "update"
    child: Optional[str] = None
    weekday: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = None
    points: Optional[int] = None
    is_conditional: bool = False


# Action Log
class ActionLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    metadata: Optional[dict]
    created_at: datetime


# Insights
class DailyStatItem(BaseModel):
    date: str
    total: int
    completed: int
    points: int


class TaskStatItem(BaseModel):
    title: str
    completed: int
    total: int
    ratio: float


class InsightsResponse(BaseModel):
    child_id: int
    period: str
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    total_points_earned: int
    daily_stats: list[DailyStatItem]
    task_stats: list[TaskStatItem]
    streak: int
