import os
import requests
from datetime import datetime
import calendar
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from modules.asset_manager import get_monthly_statistics
from utils.database import get_db_connection

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

    messages = [
        {"role": "system", "content": "You are a friendly and professional financial advisor analyzing a user's monthly budget."},
        {"role": "user", "content": prompt}
    ]

    try:
        from modules.llm_client import chat_sync
        print("[Report] Requesting report from local LLM...")
        report_content = chat_sync(messages).message.content or ""
    except Exception as e:
        print(f"[Report] LLM Error: {e}")
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

def process_recurring_payments():
    """
    매일 KST 정오(12:00)에 실행.
    오늘 날짜가 정기 결제일인 항목을 자동으로 assets에 등록하고 Discord로 알림 전송.
    월말(28~31일) 처리: 해당 월에 그 날이 없으면 말일에 실행.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    # KST 기준 오늘 날짜
    kst_now = datetime.utcnow().replace(tzinfo=None)
    # UTC+9 = KST
    from datetime import timedelta
    kst_today = (datetime.utcnow() + timedelta(hours=9)).date()

    year = kst_today.year
    month = kst_today.month
    day = kst_today.day
    last_day_of_month = calendar.monthrange(year, month)[1]

    print(f"[RecurringPayment] Checking recurring payments for KST date: {kst_today}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 오늘 실행해야 할 정기 결제 조회
            # - day_of_month == 오늘 이거나
            # - day_of_month > 이번달 말일이고 오늘이 말일인 경우 (예: 31일 설정인데 이번달이 30일까지인 경우)
            cursor.execute("""
                SELECT rp.id, rp.name, rp.cost, rp.class_id, rp.category_id,
                       rp.sub_category_id, rp.tier_id, rp.day_of_month, rp.description
                FROM recurring_payments rp
                WHERE rp.is_active = TRUE
                  AND (
                      rp.day_of_month = ?
                      OR (rp.day_of_month > ? AND ? = ?)
                  )
            """, (day, last_day_of_month, day, last_day_of_month))

            payments = cursor.fetchall()

            if not payments:
                print(f"[RecurringPayment] No recurring payments scheduled for today ({kst_today}).")
                return

            executed = []

            for p in payments:
                p = dict(p)
                payment_id = p['id']
                executed_date_str = kst_today.isoformat()

                # 이미 오늘 등록됐는지 확인 (중복 방지)
                cursor.execute("""
                    SELECT id FROM recurring_payment_logs
                    WHERE recurring_payment_id = ? AND executed_date = ?
                """, (payment_id, executed_date_str))
                if cursor.fetchone():
                    print(f"[RecurringPayment] Already executed today: {p['name']} (id={payment_id})")
                    continue

                # tier_id 결정
                tier_id = p['tier_id']
                if not tier_id and p['sub_category_id']:
                    cursor.execute("SELECT tier_id FROM asset_sub_categories WHERE id = ?", (p['sub_category_id'],))
                    row = cursor.fetchone()
                    if row:
                        tier_id = row[0]
                if not tier_id:
                    cursor.execute("SELECT tier_id FROM asset_categories WHERE id = ?", (p['category_id'],))
                    row = cursor.fetchone()
                    if row:
                        tier_id = row[0]

                # assets 테이블에 삽입
                cursor.execute("""
                    INSERT INTO assets (name, cost, class_id, category_id, sub_category_id, tier_id, date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p['name'], p['cost'], p['class_id'], p['category_id'],
                    p['sub_category_id'], tier_id, executed_date_str,
                    p['description'] or f"정기결제 자동등록"
                ))
                asset_id = cursor.lastrowid

                # 로그 기록
                cursor.execute("""
                    INSERT INTO recurring_payment_logs (recurring_payment_id, executed_date, asset_id)
                    VALUES (?, ?, ?)
                """, (payment_id, executed_date_str, asset_id))

                executed.append(p)
                print(f"[RecurringPayment] Registered: {p['name']} / {p['cost']:,.0f}원 (asset_id={asset_id})")

        # Discord 알림
        if executed and webhook_url:
            lines = [f"💳 **정기결제 자동등록** ({kst_today.strftime('%Y-%m-%d')})\n"]
            total = 0
            for p in executed:
                lines.append(f"• **{p['name']}** — {p['cost']:,.0f}원")
                total += p['cost']
            lines.append(f"\n💰 합계: **{total:,.0f}원**")

            try:
                res = requests.post(webhook_url, json={"username": "자산관리봇", "content": "\n".join(lines)})
                res.raise_for_status()
                print(f"[RecurringPayment] Discord notification sent ({len(executed)} items).")
            except Exception as e:
                print(f"[RecurringPayment] Discord notification failed: {e}")

    except Exception as e:
        print(f"[RecurringPayment] Error: {e}")


def init_scheduler():
    """
    서버 시작 시 스케줄러를 등록합니다.
    매월 마지막 날 밤 11시 50분 또는 매월 1일 자정 등 원하는 시간으로 설정 가능.
    현재는 매월 마지막 날 (last day) 23시 50분에 트리거되도록 설정.
    """
    scheduler = BackgroundScheduler()

    # 매월 마지막 날 23:50에 월간 리포트 전송
    scheduler.add_job(
        send_monthly_report_to_discord,
        trigger='cron',
        day='last',
        hour=23,
        minute=50,
        id='monthly_discord_report'
    )

    # 매일 KST 12:00 (= UTC 03:00)에 정기 결제 자동 등록
    scheduler.add_job(
        process_recurring_payments,
        trigger=CronTrigger(hour=3, minute=0, timezone='UTC'),
        id='recurring_payment_processor',
        replace_existing=True
    )

    scheduler.start()
    print("[Report] Monthly report scheduler initialized.")
    print("[RecurringPayment] Recurring payment scheduler initialized (KST 12:00 daily).")
