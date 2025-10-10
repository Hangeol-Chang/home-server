from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ScheduleType(str, Enum):
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    EVENT = "event"

class SchedulePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ScheduleStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ScheduleBase(BaseModel):
    title: str
    description: Optional[str] = None
    schedule_type: ScheduleType
    start_time: datetime
    end_time: Optional[datetime] = None
    priority: SchedulePriority = SchedulePriority.MEDIUM
    location: Optional[str] = None
    attendees: Optional[List[str]] = []
    status: ScheduleStatus = ScheduleStatus.PENDING

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: Optional[SchedulePriority] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    status: Optional[ScheduleStatus] = None

class Schedule(ScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True