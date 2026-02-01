from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# --- Recurring Schedules ---
class RecurringScheduleBase(BaseModel):
    title: str
    description: Optional[str] = None
    cycle_weeks: int = 1
    day_of_week: Optional[int] = None # 0: Mon, 6: Sun
    start_date: date
    is_active: bool = True

class RecurringScheduleCreate(RecurringScheduleBase):
    pass

class RecurringScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cycle_weeks: Optional[int] = None
    day_of_week: Optional[int] = None
    start_date: Optional[date] = None
    is_active: Optional[bool] = None

class RecurringSchedule(RecurringScheduleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Schedule Logs ---
class ScheduleLogBase(BaseModel):
    schedule_id: int
    cycle_start_date: date
    is_completed: bool = False
    notes: Optional[str] = None

class ScheduleLogCreate(ScheduleLogBase):
    pass

class ScheduleLogUpdate(BaseModel):
    is_completed: Optional[bool] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

class ScheduleLog(ScheduleLogBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Long Term Plans ---
class LongTermPlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    color: Optional[str] = None

class LongTermPlanCreate(LongTermPlanBase):
    pass

class LongTermPlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    color: Optional[str] = None

class LongTermPlan(LongTermPlanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Todo Items ---
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    color: Optional[str] = "#10B981"  # 기본 녹색
    is_completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    color: Optional[str] = None
    is_completed: Optional[bool] = None

class Todo(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
