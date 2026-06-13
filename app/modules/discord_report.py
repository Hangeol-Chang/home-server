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
    import re
    from modules.llm_client import chat_sync
    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise financial advisor. "
                "Respond ONLY with the final report in Korean. "
                "Do NOT show reasoning, thinking steps, or draft process. "
                "Output only the finished message."
            )
        },
        # /no_think: Qwen3 thinking 모드 비활성화
        {"role": "user", "content": prompt + "\n/no_think"},
    ]
    print(f"[Report] Requesting {period_label} report from LLM...")
    result = chat_sync(messages)
    content = result.message.content or ""
    # <think>...</think> 제거 (태그가 있는 경우)
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # 태그 없이 사고 과정이 노출된 경우: 첫 번째 이모지 헤더 이전 텍스트 제거
    # (실제 리포트는 항상 이모지로 시작하도록 프롬프트를 구성함)
    emoji_header = re.search(r"(?m)^[📊📅💰📉📈🗓]", content)
    if emoji_header:
        content = content[emoji_header.start():]
    return content.strip()


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

    prompt = f"""아래 데이터를 바탕으로 {year}년 {month}월 월간 지출 리포트를 Discord 메시지로 작성하세요.

작성 규칙:
- 지출 항목만 다룰 것. 수입·저축·응원·격려 문구는 포함하지 말 것.
- 총 지출액과 카테고리별 금액·비중을 명시할 것
- 지출 패턴에서 눈에 띄는 점(비중이 큰 항목, 이례적 지출 등)을 간략히 분석할 것
- 이모지와 마크다운 사용, 600자 이내

데이터:
총 지출: {stats['spend_total']:,.0f}원
카테고리별 지출:
{cats_text}"""

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

    prompt = f"""아래 데이터를 바탕으로 {week_start}~{week_end} 주간 지출 리포트를 Discord 메시지로 작성하세요.

작성 규칙:
- 지출 항목만 다룰 것. 수입·저축·응원·격려 문구는 포함하지 말 것.
- 총 지출액과 카테고리별 금액·비중을 명시할 것
- 지출 패턴에서 눈에 띄는 점(비중이 큰 항목, 이례적 지출 등)을 간략히 분석할 것
- 이모지와 마크다운 사용, 400자 이내

데이터:
총 지출: {stats['spend_total']:,.0f}원
카테고리별 지출:
{cats_text}"""

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


def generate_custom_report(user_prompt: str, send_discord: bool = True) -> str:
    """사용자 정의 프롬프트로 최근 6개월 거래 데이터를 분석합니다."""
    from datetime import date
    import calendar as _calendar

    today = date.today()
    start_month = today.month - 6
    start_year = today.year
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = f"{start_year}-{start_month:02d}-01"
    end_date = today.isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.date, ac.name as class_name,
                   ac_cat.display_name as category,
                   COALESCE(ac_sub.name, '') as sub_category,
                   a.name, a.cost
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories ac_cat ON a.category_id = ac_cat.id
            LEFT JOIN asset_sub_categories ac_sub ON a.sub_category_id = ac_sub.id
            WHERE a.date BETWEEN ? AND ?
            ORDER BY a.date DESC
            LIMIT 600
        """, (start_date, end_date))
        rows = cursor.fetchall()

    if not rows:
        return "⚠️ 분석할 거래 데이터가 없습니다."

    type_label = {'spend': '지출', 'earn': '수입', 'save': '저축'}
    lines = []
    for r in rows:
        r = dict(r)
        sub = f">{r['sub_category']}" if r['sub_category'] else ""
        lines.append(
            f"{r['date']}|{type_label.get(r['class_name'], r['class_name'])}|"
            f"{r['category']}{sub}|{r['name']}|{r['cost']:,.0f}원"
        )
    data_text = "\n".join(lines)

    prompt = f"""아래는 {start_date} ~ {end_date} 거래 내역입니다. 이 데이터로 다음 요청을 분석해 주세요.

요청: {user_prompt}

거래 내역 (날짜|유형|카테고리|항목명|금액):
{data_text}

규칙: Discord 메시지 형식(마크다운+이모지), 한국어, 500자 이내"""

    try:
        content = _call_llm(prompt, "커스텀")
    except Exception as e:
        print(f"[Report] LLM Error: {e}")
        content = f"⚠️ 분석 중 오류가 발생했습니다.\n```{e}```"

    if send_discord:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if webhook_url:
            try:
                _send_discord_chunked(webhook_url, content, username="AI 재무비서 (커스텀)")
                print("[Report] Custom report sent to Discord.")
            except Exception as e:
                print(f"[Report] Discord send error: {e}")

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
