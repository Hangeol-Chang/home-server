from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import os
import requests
from datetime import datetime

router = APIRouter(
    prefix="/test",
    tags=["Test Modules"],
    responses={404: {"description": "Not found"}}
)


@router.post("/discord-webhook")
def check_discord_webhook():
    """디스코드 웹훅의 정상 작동 여부를 테스트합니다."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url or webhook_url == "여기에_웹훅_주소를_입력해주세요":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DISCORD_WEBHOOK_URL 환경 변수가 올바르게 설정되지 않았습니다."
        )

    discord_payload = {
        "username": "AI 재무비서 (Test)",
        "content": "✅ **시스템 테스트 성공!**\n이 메시지는 서버의 웹훅 테스트 페이지에서 전송되었습니다."
    }

    try:
        response = requests.post(webhook_url, json=discord_payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discord Webhook 전송 실패: {str(e)}"
        )

    return {"message": "디스코드 테스트 메시지를 성공적으로 전송했습니다.", "status": "success"}


class MonthlyReportRequest(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    send_discord: bool = True


class WeeklyReportRequest(BaseModel):
    week_start: str  # YYYY-MM-DD
    week_end: str    # YYYY-MM-DD
    send_discord: bool = True


@router.post("/monthly-report")
def trigger_monthly_report(req: MonthlyReportRequest = None):
    """
    월간 리포트를 즉시 생성합니다.
    year/month 미지정 시 현재 달 기준. 생성된 리포트 내용을 반환합니다.
    """
    from modules.discord_report import generate_monthly_report

    now = datetime.now()
    year  = (req.year  if req and req.year  else None) or now.year
    month = (req.month if req and req.month else None) or now.month
    send_discord = req.send_discord if req is not None else True

    try:
        content = generate_monthly_report(year, month, send_discord=send_discord)
        return {"content": content, "year": year, "month": month, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/weekly-report")
def trigger_weekly_report(req: WeeklyReportRequest):
    """
    주간 리포트를 즉시 생성합니다.
    week_start / week_end: 'YYYY-MM-DD' 형식. 생성된 리포트 내용을 반환합니다.
    """
    from modules.discord_report import generate_weekly_report

    try:
        content = generate_weekly_report(req.week_start, req.week_end, send_discord=req.send_discord)
        return {
            "content": content,
            "week_start": req.week_start,
            "week_end": req.week_end,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
