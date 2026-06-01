import os
import requests
from datetime import datetime, date, timedelta
import calendar
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.database import get_db_connection


# ── 통계 헬퍼 ──────────────────────────────────────────────────────────────

def get_period_statistics(start_date: str, end_date: str) -> dict:
    """지정 날짜 범위의 재무 통계를 반환합니다."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        def _sum(class_name):
            cursor.execute("""
                SELECT COALESCE(SUM(a.cost), 0)
                FROM assets a JOIN asset_classes ac ON a.class_id = ac.id
                WHERE ac.name = ? AND a.date BETWEEN ? AND ?
            """, (class_name, start_date, end_date))
            return cursor.fetchone()[0]

        spend_total = _sum('spend')
        earn_total  = _sum('earn')
        save_total  = _sum('save')

        cursor.execute("""
            SELECT ac_cat.display_name, COALESCE(SUM(a.cost), 0) as total
            FROM assets a
            JOIN asset_classes ac       ON a.class_id    = ac.id
            JOIN asset_categories ac_cat ON a.category_id = ac_cat.id
            WHERE ac.name = 'spend' AND a.date BETWEEN ? AND ?
            GROUP BY ac_cat.id
            ORDER BY total DESC
        """, (start_date, end_date))
        categories = [{"name": row[0], "total": row[1]} for row in cursor.fetchall()]

        return {
            "earn_total":  earn_total,
            "spend_total": spend_total,
            "save_total":  save_total,
            "balance":     earn_total - spend_total - save_total,
            "categories":  categories,
        }


# ── Discord 전송 헬퍼 ───────────────────────────────────────────────────────

def _send_discord_chunked(webhook_url: str, content: str, username: str = "AI 재무비서"):
    """Discord 2000자 제한을 고려해 분할 전송합니다."""
    MAX_LEN = 1900
    if not content.strip():
        return

    chunks, buf = [], ""
    for line in content.split("\n"):
        candidate = (buf + "\n" + line) if buf else line
        if len(candidate) > MAX_LEN:
            if buf:
                chunks.append(buf)
            buf = line
        else:
            buf = candidate
    if buf:
        chunks.append(buf)

    for chunk in chunks:
        res = requests.post(webhook_url, json={"username": username, "content": chunk.strip()})
        res.raise_for_status()


# ── LLM 리포트 생성 ────────────────────────────────────────────────────────

def _call_llm(prompt: str, period_label: str) -> str:
    from modules.llm_client import chat_sync
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly and professional financial advisor. "
                "Always respond in Korean. Use markdown formatting and emojis appropriately."
            )
        },
        {"role": "user", "content": prompt},
    ]
    print(f"[Report] Requesting {period_label} report from LLM...")
    result = chat_sync(messages)
    return result.message.content or ""


def generate_monthly_report(year: int, month: int, send_discord: bool = True) -> str:
    """
    월간 재무 리포트를 생성합니다.
    생성된 내용을 반환하고, send_discord=True 이면 Discord에도 전송합니다.
    """
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day:02d}"

    stats = get_period_statistics(start, end)
    cats_text = "\n".join(
        f"  - {c['name']}: {c['total']:,.0f}원" for c in stats["categories"]
    ) or "  (데이터 없음)"

    prompt = f"""다음은 나의 {year}년 {month}월 재무 통계입니다.
이 데이터를 바탕으로 친근하고 분석적인 월간 재무 리포트를 작성해 주세요.
Discord 메시지로 볼 것이므로 마크다운과 이모지를 적절히 사용하고, 1500자 이내로 작성해 주세요.

- 총 수익: {stats['earn_total']:,.0f}원
- 총 지출: {stats['spend_total']:,.0f}원
- 총 저축: {stats['save_total']:,.0f}원
- 잔액: {stats['balance']:,.0f}원
- 카테고리별 지출:
{cats_text}

인사말로 시작하고 응원의 말로 마무리해 주세요."""

    try:
        content = _call_llm(prompt, f"{year}-{month:02d} 월간")
    except Exception as e:
        print(f"[Report] LLM Error: {e}")
        content = f"⚠️ 월간 리포트를 생성하는 중 오류가 발생했습니다.\n```{e}```"

    if send_discord:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                _send_discord_chunked(webhook_url, content)
                print("[Report] Monthly report sent to Discord.")
            except Exception as e:
                print(f"[Report] Discord send error: {e}")
        else:
            print("[Report] DISCORD_WEBHOOK_URL not set, skipping Discord send.")

    return content


def generate_weekly_report(week_start: str, week_end: str, send_discord: bool = True) -> str:
    """
    주간 재무 리포트를 생성합니다.
    week_start / week_end: 'YYYY-MM-DD' 형식
    """
    stats = get_period_statistics(week_start, week_end)
    cats_text = "\n".join(
        f"  - {c['name']}: {c['total']:,.0f}원" for c in stats["categories"]
    ) or "  (데이터 없음)"

    prompt = f"""다음은 나의 {week_start} ~ {week_end} 주간 재무 통계입니다.
이 데이터를 바탕으로 친근하고 분석적인 주간 재무 리포트를 작성해 주세요.
Discord 메시지로 볼 것이므로 마크다운과 이모지를 적절히 사용하고, 1200자 이내로 작성해 주세요.

- 총 수익: {stats['earn_total']:,.0f}원
- 총 지출: {stats['spend_total']:,.0f}원
- 총 저축: {stats['save_total']:,.0f}원
- 잔액: {stats['balance']:,.0f}원
- 카테고리별 지출:
{cats_text}

이번 주 소비 패턴을 간략히 분석하고 응원의 말로 마무리해 주세요."""

    try:
        content = _call_llm(prompt, f"{week_start}~{week_end} 주간")
    except Exception as e:
        print(f"[Report] LLM Error: {e}")
        content = f"⚠️ 주간 리포트를 생성하는 중 오류가 발생했습니다.\n```{e}```"

    if send_discord:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                _send_discord_chunked(webhook_url, content, username="AI 재무비서 (주간)")
                print("[Report] Weekly report sent to Discord.")
            except Exception as e:
                print(f"[Report] Discord send error: {e}")
        else:
            print("[Report] DISCORD_WEBHOOK_URL not set, skipping Discord send.")

    return content


# ── 스케줄러용 래퍼 ────────────────────────────────────────────────────────

def send_monthly_report_to_discord():
    """매월 말일 자동 실행용. 이번 달 리포트를 Discord로 전송합니다."""
    now = datetime.now()
    generate_monthly_report(now.year, now.month, send_discord=True)


# ── 정기결제 자동 처리 ─────────────────────────────────────────────────────

def process_recurring_payments():
    """
    매일 KST 정오(12:00)에 실행.
    오늘 날짜가 정기 결제일인 항목을 자동으로 assets에 등록하고 Discord로 알림 전송.
    월말(28~31일) 처리: 해당 월에 그 날이 없으면 말일에 실행.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    kst_today = (datetime.utcnow() + timedelta(hours=9)).date()

    year  = kst_today.year
    month = kst_today.month
    day   = kst_today.day
    last_day_of_month = calendar.monthrange(year, month)[1]

    print(f"[RecurringPayment] Checking recurring payments for KST date: {kst_today}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

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

                cursor.execute("""
                    SELECT id FROM recurring_payment_logs
                    WHERE recurring_payment_id = ? AND executed_date = ?
                """, (payment_id, executed_date_str))
                if cursor.fetchone():
                    print(f"[RecurringPayment] Already executed today: {p['name']} (id={payment_id})")
                    continue

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

                cursor.execute("""
                    INSERT INTO assets (name, cost, class_id, category_id, sub_category_id, tier_id, date, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p['name'], p['cost'], p['class_id'], p['category_id'],
                    p['sub_category_id'], tier_id, executed_date_str,
                    p['description'] or "정기결제 자동등록"
                ))
                asset_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO recurring_payment_logs (recurring_payment_id, executed_date, asset_id)
                    VALUES (?, ?, ?)
                """, (payment_id, executed_date_str, asset_id))

                executed.append(p)
                print(f"[RecurringPayment] Registered: {p['name']} / {p['cost']:,.0f}원 (asset_id={asset_id})")

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


# ── 스케줄러 초기화 ────────────────────────────────────────────────────────

def init_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        send_monthly_report_to_discord,
        trigger='cron',
        day='last',
        hour=23,
        minute=50,
        id='monthly_discord_report'
    )

    scheduler.add_job(
        process_recurring_payments,
        trigger=CronTrigger(hour=3, minute=0, timezone='UTC'),
        id='recurring_payment_processor',
        replace_existing=True
    )

    scheduler.start()
    print("[Report] Monthly report scheduler initialized.")
    print("[RecurringPayment] Recurring payment scheduler initialized (KST 12:00 daily).")
