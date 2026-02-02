from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
import os
import requests
from icalendar import Calendar
from models.schedule import (
    RecurringSchedule, RecurringScheduleCreate, RecurringScheduleUpdate,
    ScheduleLog, ScheduleLogCreate, ScheduleLogUpdate,
    LongTermPlan, LongTermPlanCreate, LongTermPlanUpdate,
    Todo, TodoCreate, TodoUpdate,
    WeeklySchedule, WeeklyScheduleCreate, WeeklyScheduleUpdate
)
from utils.database import get_db_connection
import sqlite3

router = APIRouter(
    prefix="/schedule-manager",
    tags=["Schedule Manager"],
    responses={404: {"description": "Not found"}}
)

# --- Recurring Schedules ---

@router.get("/recurring-schedules", response_model=List[RecurringSchedule])
async def get_recurring_schedules(active_only: bool = True):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM recurring_schedules"
        if active_only:
            query += " WHERE is_active = 1"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/recurring-schedules", response_model=RecurringSchedule, status_code=status.HTTP_201_CREATED)
async def create_recurring_schedule(schedule: RecurringScheduleCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recurring_schedules (title, description, cycle_weeks, day_of_week, start_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (schedule.title, schedule.description, schedule.cycle_weeks, schedule.day_of_week, schedule.start_date, schedule.is_active))
        schedule_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM recurring_schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        return dict(row)

@router.put("/recurring-schedules/{schedule_id}", response_model=RecurringSchedule)
async def update_recurring_schedule(schedule_id: int, schedule: RecurringScheduleUpdate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT * FROM recurring_schedules WHERE id = ?", (schedule_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Schedule not found")
            
        update_data = schedule.dict(exclude_unset=True)
        if not update_data:
            cursor.execute("SELECT * FROM recurring_schedules WHERE id = ?", (schedule_id,))
            return dict(cursor.fetchone())

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(schedule_id)
        
        cursor.execute(f"UPDATE recurring_schedules SET {set_clause} WHERE id = ?", values)
        
        cursor.execute("SELECT * FROM recurring_schedules WHERE id = ?", (schedule_id,))
        return dict(cursor.fetchone())

@router.delete("/recurring-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_schedule(schedule_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recurring_schedules WHERE id = ?", (schedule_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")

# --- Schedule Logs ---

@router.get("/schedule-logs", response_model=List[ScheduleLog])
async def get_schedule_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    schedule_id: Optional[int] = None
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM schedule_logs WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND cycle_start_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND cycle_start_date <= ?"
            params.append(end_date)
        if schedule_id:
            query += " AND schedule_id = ?"
            params.append(schedule_id)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/schedule-logs", response_model=ScheduleLog)
async def create_or_update_log(log: ScheduleLogCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if log already exists for this schedule and cycle
        cursor.execute("""
            SELECT id FROM schedule_logs 
            WHERE schedule_id = ? AND cycle_start_date = ?
        """, (log.schedule_id, log.cycle_start_date))
        existing = cursor.fetchone()
        
        now = datetime.now()
        
        if existing:
            # Update
            log_id = existing[0]
            completed_at = now if log.is_completed else None
            cursor.execute("""
                UPDATE schedule_logs 
                SET is_completed = ?, notes = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
            """, (log.is_completed, log.notes, completed_at, now, log_id))
        else:
            # Create
            completed_at = now if log.is_completed else None
            cursor.execute("""
                INSERT INTO schedule_logs (schedule_id, cycle_start_date, is_completed, notes, completed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (log.schedule_id, log.cycle_start_date, log.is_completed, log.notes, completed_at))
            log_id = cursor.lastrowid
            
        cursor.execute("SELECT * FROM schedule_logs WHERE id = ?", (log_id,))
        return dict(cursor.fetchone())

# --- Long Term Plans ---

@router.get("/long-term-plans", response_model=List[LongTermPlan])
async def get_long_term_plans(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM long_term_plans WHERE 1=1"
        params = []
        
        # Overlap check: (StartA <= EndB) and (EndA >= StartB)
        if start_date and end_date:
            query += " AND start_date <= ? AND end_date >= ?"
            params.extend([end_date, start_date])
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/long-term-plans", response_model=LongTermPlan, status_code=status.HTTP_201_CREATED)
async def create_long_term_plan(plan: LongTermPlanCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO long_term_plans (title, description, start_date, end_date, color)
            VALUES (?, ?, ?, ?, ?)
        """, (plan.title, plan.description, plan.start_date, plan.end_date, plan.color))
        plan_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM long_term_plans WHERE id = ?", (plan_id,))
        return dict(cursor.fetchone())

@router.put("/long-term-plans/{plan_id}", response_model=LongTermPlan)
async def update_long_term_plan(plan_id: int, plan: LongTermPlanUpdate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM long_term_plans WHERE id = ?", (plan_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
            
        update_data = plan.dict(exclude_unset=True)
        if not update_data:
            cursor.execute("SELECT * FROM long_term_plans WHERE id = ?", (plan_id,))
            return dict(cursor.fetchone())

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(plan_id)
        
        cursor.execute(f"UPDATE long_term_plans SET {set_clause} WHERE id = ?", values)
        
        cursor.execute("SELECT * FROM long_term_plans WHERE id = ?", (plan_id,))
        return dict(cursor.fetchone())

@router.delete("/long-term-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_long_term_plan(plan_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM long_term_plans WHERE id = ?", (plan_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Plan not found")

# --- Google Calendar Events ---

@router.get("/google-events")
async def get_google_events(year: int, month: int):
    """
    Fetch events from Google Calendar via iCal URL.
    Requires GOOGLE_CALENDAR_ICS_URL environment variable.
    """
    ics_url = os.getenv("GOOGLE_CALENDAR_ICS_URL")
    if not ics_url:
        print("GOOGLE_CALENDAR_ICS_URL not set")
        return []

    try:
        response = requests.get(ics_url)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        
        events = []
        
        # Calculate month range
        # We want to include events that overlap with this month
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
            
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary'))
                dtstart_prop = component.get('dtstart')
                dtend_prop = component.get('dtend')
                
                if not dtstart_prop:
                    continue
                    
                dtstart = dtstart_prop.dt
                
                if dtend_prop:
                    dtend = dtend_prop.dt
                else:
                    # If no end date, assume 1 day (or same time)
                    dtend = dtstart

                # Normalize to date objects
                if isinstance(dtstart, datetime):
                    start_d = dtstart.date()
                else:
                    start_d = dtstart
                
                if isinstance(dtend, datetime):
                    end_d = dtend.date()
                else:
                    end_d = dtend
                    # For all-day events (date type), dtend is exclusive in iCal
                    # We want inclusive for our frontend logic
                    end_d = end_d - timedelta(days=1)
                
                # Check overlap with the requested month
                # (Start <= MonthEnd) and (End >= MonthStart)
                if start_d <= month_end and end_d >= month_start:
                    events.append({
                        "title": summary,
                        "start_date": start_d.isoformat(),
                        "end_date": end_d.isoformat(),
                        "color": "#4285F4", # Google Blue
                        "source": "google"
                    })
                    
        return events

    except Exception as e:
        print(f"Error fetching Google Calendar: {e}")
        return []


@router.get("/google-events/week")
async def get_google_events_for_week(start_date: date, end_date: date):
    """
    Fetch events from Google Calendar via iCal URL for a specific date range.
    """
    ics_url = os.getenv("GOOGLE_CALENDAR_ICS_URL")
    if not ics_url:
        print("GOOGLE_CALENDAR_ICS_URL not set")
        return []

    try:
        response = requests.get(ics_url)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        
        events = []
            
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary'))
                dtstart_prop = component.get('dtstart')
                dtend_prop = component.get('dtend')
                
                if not dtstart_prop:
                    continue
                    
                dtstart = dtstart_prop.dt
                
                if dtend_prop:
                    dtend = dtend_prop.dt
                else:
                    dtend = dtstart

                # Normalize to date objects
                if isinstance(dtstart, datetime):
                    start_d = dtstart.date()
                else:
                    start_d = dtstart
                
                if isinstance(dtend, datetime):
                    end_d = dtend.date()
                else:
                    end_d = dtend
                    end_d = end_d - timedelta(days=1)
                
                # Check overlap with the requested range
                if start_d <= end_date and end_d >= start_date:
                    events.append({
                        "title": summary,
                        "start_date": start_d.isoformat(),
                        "end_date": end_d.isoformat(),
                        "color": "#4285F4",
                        "source": "google"
                    })
                    
        return events

    except Exception as e:
        print(f"Error fetching Google Calendar: {e}")
        return []


# --- Todo Items ---

@router.get("/todos", response_model=List[Todo])
async def get_todos(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_completed: bool = True
):
    """지정된 날짜 범위의 할일 목록 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM todos WHERE 1=1"
        params = []
        
        # Overlap check: (StartA <= EndB) and (EndA >= StartB)
        if start_date and end_date:
            query += " AND start_date <= ? AND end_date >= ?"
            params.extend([end_date, start_date])
        
        if not include_completed:
            query += " AND is_completed = 0"
            
        query += " ORDER BY start_date, created_at"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    """새 할일 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute("""
            INSERT INTO todos (title, description, start_date, end_date, color, is_completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (todo.title, todo.description, todo.start_date, todo.end_date, todo.color, todo.is_completed, now, now))
        todo_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        return dict(cursor.fetchone())


@router.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int):
    """특정 할일 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        return dict(row)


@router.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoUpdate):
    """할일 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
            
        update_data = todo.dict(exclude_unset=True)
        if not update_data:
            cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
            return dict(cursor.fetchone())

        update_data['updated_at'] = datetime.now()
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(todo_id)
        
        cursor.execute(f"UPDATE todos SET {set_clause} WHERE id = ?", values)
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        return dict(cursor.fetchone())


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int):
    """할일 삭제"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")


@router.patch("/todos/{todo_id}/toggle", response_model=Todo)
async def toggle_todo_completion(todo_id: int):
    """할일 완료 상태 토글"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        new_status = not row['is_completed']
        now = datetime.now()
        cursor.execute("UPDATE todos SET is_completed = ?, updated_at = ? WHERE id = ?", (new_status, now, todo_id))
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        return dict(cursor.fetchone())


@router.patch("/todos/{todo_id}/move", response_model=Todo)
async def move_todo(todo_id: int, new_start_date: date, new_end_date: date):
    """할일 날짜 이동 (드래그 앤 드롭용)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
        
        now = datetime.now()
        cursor.execute("""
            UPDATE todos SET start_date = ?, end_date = ?, updated_at = ? WHERE id = ?
        """, (new_start_date, new_end_date, now, todo_id))
        
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        return dict(cursor.fetchone())


# --- Weekly Timetable Schedules ---

@router.get("/weekly-schedules", response_model=List[WeeklySchedule])
async def get_weekly_schedules():
    """주간 타임테이블 일정 목록 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM weekly_schedules ORDER BY day_of_week, start_time")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/weekly-schedules", response_model=WeeklySchedule, status_code=status.HTTP_201_CREATED)
async def create_weekly_schedule(schedule: WeeklyScheduleCreate):
    """새 주간 타임테이블 일정 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute("""
            INSERT INTO weekly_schedules (title, description, day_of_week, start_time, end_time, color, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (schedule.title, schedule.description, schedule.day_of_week, schedule.start_time, schedule.end_time, schedule.color, now, now))
        schedule_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM weekly_schedules WHERE id = ?", (schedule_id,))
        return dict(cursor.fetchone())


@router.get("/weekly-schedules/{schedule_id}", response_model=WeeklySchedule)
async def get_weekly_schedule(schedule_id: int):
    """특정 주간 타임테이블 일정 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM weekly_schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Weekly schedule not found")
        return dict(row)


@router.put("/weekly-schedules/{schedule_id}", response_model=WeeklySchedule)
async def update_weekly_schedule(schedule_id: int, schedule: WeeklyScheduleUpdate):
    """주간 타임테이블 일정 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM weekly_schedules WHERE id = ?", (schedule_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Weekly schedule not found")
            
        update_data = schedule.dict(exclude_unset=True)
        if not update_data:
            cursor.execute("SELECT * FROM weekly_schedules WHERE id = ?", (schedule_id,))
            return dict(cursor.fetchone())

        update_data['updated_at'] = datetime.now()
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(schedule_id)
        
        cursor.execute(f"UPDATE weekly_schedules SET {set_clause} WHERE id = ?", values)
        
        cursor.execute("SELECT * FROM weekly_schedules WHERE id = ?", (schedule_id,))
        return dict(cursor.fetchone())


@router.delete("/weekly-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weekly_schedule(schedule_id: int):
    """주간 타임테이블 일정 삭제"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weekly_schedules WHERE id = ?", (schedule_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Weekly schedule not found")

