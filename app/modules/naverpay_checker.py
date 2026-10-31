import os
import re
import imaplib
import email
from datetime import datetime, timedelta, timezone
import requests
from utils.database import get_db_connection

SENDER = "naverpayadmin_noreply@navercorp.com"
FOLDER = '"&zK2tbAC3rLDIHA-"'  # "청구·결제" (IMAP modified UTF-7), 네이버 메일 규칙으로 분류됨
KST = timezone(timedelta(hours=9))


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def parse_naverpay(html: str):
    """네이버페이 결제 메일 → {merchant, cost, paid_at(YYYY-MM-DD), pay_no} (실패 시 None)"""
    t = _text(html)
    m = re.search(r"가맹점명\s+(.+?)\s+총 결제 금액\s+([\d,]+)\s*원", t)
    d = re.search(r"결제일자\s+(\d{4})\.(\d{2})\.(\d{2})", t)
    n = re.search(r"결제번호\s+(\w+)", t)
    if not (m and d):
        return None
    return {
        "merchant": m.group(1).strip(),
        "cost": int(m.group(2).replace(",", "")),
        "date": f"{d.group(1)}-{d.group(2)}-{d.group(3)}",
        "pay_no": n.group(1) if n else "",
    }


def fetch_payments(day) -> list:
    """해당 날짜(KST)에 온 네이버페이 결제 메일을 파싱해 반환"""
    since = day.strftime("%d-%b-%Y")
    before = (day + timedelta(days=1)).strftime("%d-%b-%Y")
    out = []
    imap = imaplib.IMAP4_SSL("imap.naver.com", 993)
    try:
        imap.login(os.getenv("NAVER_EMAIL_ADDRESS"), os.getenv("NAVER_EMAIL_PASSWORD"))
        imap.select(FOLDER, readonly=True)  # 읽음 상태 변경 방지
        _, data = imap.search(None, "FROM", SENDER, "SINCE", since, "BEFORE", before)
        for uid in data[0].split():
            _, msg_data = imap.fetch(uid, "(BODY.PEEK[])")
            msg = email.message_from_bytes(msg_data[0][1])
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                    p = parse_naverpay(html)
                    if p:
                        out.append(p)
                    else:
                        print(f"[NaverPay] 파싱 실패 uid={uid.decode()}")
                    break
    finally:
        try:
            imap.logout()
        except Exception:
            pass
    return out


def check_naverpay():
    """어제 네이버페이 결제 중 assets에 (날짜+금액) 일치 항목이 없는 것을 Discord로 알림"""
    try:
        yesterday = (datetime.now(KST) - timedelta(days=1)).date()
        payments = fetch_payments(yesterday)
        missing = []
        with get_db_connection() as conn:
            cur = conn.cursor()
            for p in payments:
                cur.execute("SELECT 1 FROM assets WHERE date = ? AND cost = ? LIMIT 1", (p["date"], p["cost"]))
                if not cur.fetchone():
                    missing.append(p)
        print(f"[NaverPay] {yesterday}: 결제 {len(payments)}건, 미등록 {len(missing)}건")

        webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if missing and webhook:
            lines = [f"🧾 **네이버페이 미등록 결제 의심** ({yesterday})\n"]
            lines += [f"• **{p['merchant']}** — {p['cost']:,}원 ({p['date']})" for p in missing]
            requests.post(webhook, json={"username": "자산관리봇", "content": "\n".join(lines)}).raise_for_status()
    except Exception as e:
        print(f"[NaverPay] Error: {e}")


if __name__ == "__main__":
    # 파서 self-check (실제 메일 구조 축약본)
    sample = """<td>가맹점명</td><td> 주식회사 자광건설 </td><td>총 결제 금액</td>
    <td><span>4,500</span>원</td> 결제번호 <a>20261031NP1840740991</a> 결제일자 </td><td> 2026.10.31 15:36"""
    assert parse_naverpay(sample) == {"merchant": "주식회사 자광건설", "cost": 4500,
                                      "date": "2026-10-31", "pay_no": "20261031NP1840740991"}
    print("ok")
