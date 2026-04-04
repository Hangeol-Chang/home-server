import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from modules.asset_manager import get_monthly_statistics

def send_monthly_report_to_discord():
    """
    매월 말일(또는 다음달 1일)에 실행하여
    1. 이번 달 소비 통계를 가져옴
    2. Ollama (llama3.1:8b) 로 리포트 생성
    3. Discord Webhook 으로 전송
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[Report] DISCORD_WEBHOOK_URL is not set. Skipping report.")
        return

    now = datetime.now()
    year = now.year
    month = now.month

    # 1. 이번 달 소비 통계 가져오기
    try:
        # get_monthly_statistics 함수가 dict 형태를 반환한다고 가정
        stats = get_monthly_statistics(year=year, month=month)
    except Exception as e:
        print(f"[Report] Failed to get monthly statistics: {e}")
        return

    # 지출/수익 데이터 구성 (통계 데이터 구조에 맞게 조정 필요 가능)
    spend_total = stats.get('spend_total', 0)
    income_total = stats.get('income_total', 0)
    save_total = stats.get('save_total', 0)
    categories = stats.get('categories', [])

    # 2. Ollama (llama3.1:8b) 로 리포트 생성
    prompt = f"""
다음은 나의 {year}년 {month}월 재무 통계입니다. 이 데이터를 바탕으로 나를 칭찬하고 개선점을 조언해 주는 친근하고 분석적인 월간 재무 리포트를 작성해주세요. 
Discord 메시지로 보낼 것이므로 마크다운과 이모지를 적절히 사용해주세요.

- 총 수익: {income_total}원
- 총 지출: {spend_total}원
- 총 저축: {save_total}원
- 카테고리별 지출 요약:
{categories}

(반드시 한국어로 작성하고, 인사말로 시작해서 응원의 말로 마무리해주세요.)
"""

    # 디스코드 리포트용 모델 환경변수 (기본값: llama3.1:8b)
    report_model = os.getenv("OLLAMA_MODEL_REPORT", "llama3.1:8b")

    payload = {
        "model": report_model,
        "messages": [
            {"role": "system", "content": "You are a friendly and professional financial advisor analyzing a user's monthly budget."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        print(f"[Report] Requesting report from Ollama ({report_model})...")
        response = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=300)
        response.raise_for_status()
        report_content = response.json().get("message", {}).get("content", "")
    except Exception as e:
        print(f"[Report] Ollama Error: {e}")
        report_content = f"⚠️ 월간 리포트를 생성하는 중 오류가 발생했습니다.\n```{e}```"

    # 3. Discord 로 전송
    discord_payload = {
        "username": "AI 재무비서",
        "content": report_content
    }

    try:
        discord_res = requests.post(webhook_url, json=discord_payload)
        discord_res.raise_for_status()
        print("[Report] Successfully sent monthly report to Discord.")
    except Exception as e:
        print(f"[Report] Discord Webhook Error: {e}")

def init_scheduler():
    """
    서버 시작 시 스케줄러를 등록합니다.
    매월 마지막 날 밤 11시 50분 또는 매월 1일 자정 등 원하는 시간으로 설정 가능.
    현재는 매월 마지막 날 (last day) 23시 50분에 트리거되도록 설정.
    """
    scheduler = BackgroundScheduler()
    # 매월 마지막 날 23:50 에 실행
    scheduler.add_job(
        send_monthly_report_to_discord,
        trigger='cron',
        day='last',
        hour=23,
        minute=50,
        id='monthly_discord_report'
    )
    scheduler.start()
    print("[Report] Monthly report scheduler initialized.")
