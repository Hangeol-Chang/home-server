from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from models.schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleStatus, SchedulePriority

# 라우터 생성
router = APIRouter(
    prefix="/schedule-manager",
    tags=["Schedule Manager"],
    responses={404: {"description": "Not found"}}
)

# 메모리 기반 임시 데이터베이스
schedules_db = []
next_schedule_id = 1

@router.get("/", response_model=List[Schedule])
async def get_all_schedules():
    """모든 일정 조회"""
    return schedules_db

@router.get("/schedules", response_model=List[Schedule])
async def get_schedules(
    status: Optional[ScheduleStatus] = None,
    priority: Optional[SchedulePriority] = None,
    start_date: Optional[date] = Query(None, description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="조회 종료 날짜 (YYYY-MM-DD)")
):
    """일정 조회 (필터링 옵션 포함)"""
    filtered_schedules = schedules_db.copy()
    
    # 상태 필터
    if status:
        filtered_schedules = [s for s in filtered_schedules if s["status"] == status]
    
    # 우선순위 필터
    if priority:
        filtered_schedules = [s for s in filtered_schedules if s["priority"] == priority]
    
    # 날짜 범위 필터
    if start_date:
        filtered_schedules = [s for s in filtered_schedules 
                            if s["start_time"].date() >= start_date]
    
    if end_date:
        filtered_schedules = [s for s in filtered_schedules 
                            if s["start_time"].date() <= end_date]
    
    return filtered_schedules

@router.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: int):
    """특정 일정 조회"""
    for schedule in schedules_db:
        if schedule["id"] == schedule_id:
            return schedule
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Schedule with id {schedule_id} not found"
    )

@router.post("/schedules", response_model=Schedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: ScheduleCreate):
    """새 일정 생성"""
    global next_schedule_id
    
    # 시간 유효성 검사
    if schedule.end_time and schedule.end_time <= schedule.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    now = datetime.now()
    schedule_dict = schedule.dict()
    schedule_dict.update({
        "id": next_schedule_id,
        "created_at": now,
        "updated_at": now
    })
    
    next_schedule_id += 1
    schedules_db.append(schedule_dict)
    
    return schedule_dict

@router.put("/schedules/{schedule_id}", response_model=Schedule)
async def update_schedule(schedule_id: int, schedule_update: ScheduleUpdate):
    """일정 정보 수정"""
    for i, schedule in enumerate(schedules_db):
        if schedule["id"] == schedule_id:
            # 업데이트할 필드만 적용
            update_data = schedule_update.dict(exclude_unset=True)
            
            # 시간 유효성 검사
            if update_data:
                start_time = update_data.get("start_time", schedule["start_time"])
                end_time = update_data.get("end_time", schedule.get("end_time"))
                
                if end_time and end_time <= start_time:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="End time must be after start time"
                    )
                
                update_data["updated_at"] = datetime.now()
                schedules_db[i].update(update_data)
            
            return schedules_db[i]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Schedule with id {schedule_id} not found"
    )

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """일정 삭제"""
    for i, schedule in enumerate(schedules_db):
        if schedule["id"] == schedule_id:
            deleted_schedule = schedules_db.pop(i)
            return {
                "message": f"Schedule {schedule_id} deleted successfully",
                "deleted_schedule": deleted_schedule
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Schedule with id {schedule_id} not found"
    )

@router.get("/schedules/today", response_model=List[Schedule])
async def get_today_schedules():
    """오늘 일정 조회"""
    today = date.today()
    today_schedules = [
        schedule for schedule in schedules_db 
        if schedule["start_time"].date() == today
    ]
    return sorted(today_schedules, key=lambda x: x["start_time"])

@router.get("/schedules/upcoming", response_model=List[Schedule])
async def get_upcoming_schedules(days: int = Query(7, description="앞으로 며칠간의 일정을 조회할지")):
    """다가오는 일정 조회"""
    now = datetime.now()
    upcoming_schedules = [
        schedule for schedule in schedules_db 
        if schedule["start_time"] >= now and 
           schedule["start_time"] <= now.replace(hour=23, minute=59, second=59).replace(day=now.day + days)
    ]
    return sorted(upcoming_schedules, key=lambda x: x["start_time"])

@router.patch("/schedules/{schedule_id}/status")
async def update_schedule_status(schedule_id: int, new_status: ScheduleStatus):
    """일정 상태 변경"""
    for i, schedule in enumerate(schedules_db):
        if schedule["id"] == schedule_id:
            schedules_db[i]["status"] = new_status
            schedules_db[i]["updated_at"] = datetime.now()
            return {
                "message": f"Schedule {schedule_id} status updated to {new_status}",
                "schedule": schedules_db[i]
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Schedule with id {schedule_id} not found"
    )

@router.get("/schedules/search/{query}")
async def search_schedules(query: str):
    """일정 제목이나 설명으로 검색"""
    results = []
    query_lower = query.lower()
    
    for schedule in schedules_db:
        if (query_lower in schedule["title"].lower() or 
            (schedule.get("description") and query_lower in schedule["description"].lower()) or
            (schedule.get("location") and query_lower in schedule["location"].lower())):
            results.append(schedule)
    
    return {
        "query": query,
        "total_results": len(results),
        "results": sorted(results, key=lambda x: x["start_time"])
    }

@router.get("/stats")
async def get_schedule_stats():
    """일정 통계 정보"""
    total_schedules = len(schedules_db)
    
    if total_schedules == 0:
        return {
            "total_schedules": 0,
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "today_count": 0,
            "upcoming_count": 0
        }
    
    # 각종 통계 계산
    status_stats = {}
    priority_stats = {}
    type_stats = {}
    today = date.today()
    now = datetime.now()
    
    today_count = 0
    upcoming_count = 0
    
    for schedule in schedules_db:
        # 상태별 통계
        status = schedule["status"]
        status_stats[status] = status_stats.get(status, 0) + 1
        
        # 우선순위별 통계
        priority = schedule["priority"]
        priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        # 타입별 통계
        schedule_type = schedule["schedule_type"]
        type_stats[schedule_type] = type_stats.get(schedule_type, 0) + 1
        
        # 오늘 일정 카운트
        if schedule["start_time"].date() == today:
            today_count += 1
        
        # 다가오는 일정 카운트 (앞으로 7일)
        if schedule["start_time"] >= now and schedule["start_time"] <= now.replace(day=now.day + 7):
            upcoming_count += 1
    
    return {
        "total_schedules": total_schedules,
        "by_status": status_stats,
        "by_priority": priority_stats,
        "by_type": type_stats,
        "today_count": today_count,
        "upcoming_count": upcoming_count
    }