"""
מתמצת חדשות טלגרם אוטומטי
שולח דוח יומי פעמיים ביום: 07:00 ו-20:00
"""

import asyncio
import json
import os
import re
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

# ── הגדרות ──────────────────────────────────────────────────────────────────
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION_STRING = os.environ["TELEGRAM_SESSION"]      # StringSession מוצפן
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MY_TELEGRAM_ID = int(os.environ["MY_TELEGRAM_ID"])   # ה-User ID שלך

MEMORY_FILE = Path("seen_news.json")
HOURS_LOOKBACK = 13   # כמה שעות אחורה לקרוא מכל ערוץ

# ── זכרון ידיעות (מניעת חזרות) ──────────────────────────────────────────────
def load_memory() -> dict:
    if MEMORY_FILE.exists():
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    else:
        data = {"items": []}
    # מחיקת פריטים ישנים מעל 24 שעות
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    data["items"] = [i for i in data["items"] if i["ts"] > cutoff]
    return data

def save_memory(data: dict):
    MEMORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def news_hash(text: str) -> str:
    return hashlib.md5(text[:120].encode()).hexdigest()

def already_seen(memory: dict, text: str) -> bool:
    h = news_hash(text)
    return any(i["hash"] == h for i in memory["items"])

def add_to_memory(memory: dict, text: str):
    memory["items"].append({
        "hash": news_hash(text),
        "ts": datetime.now(timezone.utc).isoformat(),
        "preview": text[:80]
    })

# ── קריאת הודעות מטלגרם ──────────────────────────────────────────────────────
async def fetch_messages(client: TelegramClient) -> list[dict]:
    """קורא הודעות מכל הערוצים שהמשתמש מנוי עליהם"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    messages = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        # רק ערוצים וקבוצות (לא שיחות פרטיות)
        if not isinstance(entity, (Channel, Chat)):
            continue

        try:
            async for msg in client.iter_messages(entity, limit=30, offset_date=None):
                if msg.date < cutoff:
                    break
                if not msg.text or len(msg.text.strip()) < 30:
                    continue
                messages.append({
                    "channel": dialog.name,
                    "text": msg.text.strip(),
                    "date": msg.date.isoformat(),
                    "is_broadcast": getattr(entity, "broadcast", False)
                })
        except Exception:
            continue  # ערוץ חסום/פרטי

    return messages

# ── עיבוד AI ─────────────────────────────────────────────────────────────────
def build_prompt(messages: list[dict], memory: dict) -> str:
    seen_hashes = {i["hash"] for i in memory["items"]}

    # סינון ידיעות שכבר ראינו
    fresh = [m for m in messages if news_hash(m["text"]) not in seen_hashes]

    # סינון חדשות "רועשות" — אזעקות, מקלטים, חזרות תכופות
    noise_patterns = [
        r"אזעק", r"מקלט", r"ירי\s*רקטות?", r"התרעה", r"Color\s*Red",
        r"אין\s*אזעקות?", r"חזרה\s*לשגרה"
    ]
    noise_re = re.compile("|".join(noise_patterns), re.IGNORECASE)
    fresh = [m for m in fresh if not noise_re.search(m["text"])]

    if not fresh:
        return ""

    msgs_text = "\n\n".join(
        f"[{m['channel']}] {m['text'][:400]}"
        for m in fresh[:80]  # מגביל כדי לא לפוצץ את ה-context
    )

    return f"""אתה עוזר שמכין דוח חדשות יומי בעברית.

להלן הודעות מערוצי טלגרם שונים מהשעות האחרונות:
---
{msgs_text}
---

צור דוח בעברית עם שני חלקים בדיוק:

**חלק א׳ — חדשות עיקריות**
• 5–8 ידיעות חדשותיות קצרות ותמציתיות
• כל ידיעה: שורה אחת, עם שם הערוץ בסוגריים
• אל תכלול חדשות חוזרות, אזעקות, או עדכונים שוליים
• אם יש כמה ידיעות על אותו נושא — אחד אותן לידיעה אחת

**חלק ב׳ — מזג אוויר** (אם יש מידע רלוונטי בהודעות)
• אם נמצא מידע על מזג האוויר — סכם אותו בשורה אחת
• אם אין — השמט חלק זה לחלוטין

**חלק ג׳ — הרחבת אופקים**
• 2–4 פריטים מעניינים שאינם חדשות שוטפות
• נושאים: ניתוחים, כלכלה, טכנולוגיה, גיאופוליטיקה, תרבות
• כל פריט: כותרת + 2–3 משפטי הסבר
• העדף תוכן עם עומק ולא רק כותרות

החזר רק את הדוח המוגמר, ללא הסברים נוספים."""

async def process_with_ai(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

# ── שליחת הדוח ───────────────────────────────────────────────────────────────
async def send_report(client: TelegramClient, report: str):
    await client.send_message(MY_TELEGRAM_ID, report, parse_mode="markdown")

# ── main ──────────────────────────────────────────────────────────────────────
async def main():
    from telethon.sessions import StringSession

    print(f"[{datetime.now().strftime('%H:%M')}] מתחיל הרצה...")

    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as tg:
        # קריאת הודעות
        print("קורא הודעות מטלגרם...")
        messages = await fetch_messages(tg)
        print(f"נמצאו {len(messages)} הודעות")

        # זכרון
        memory = load_memory()

        # בניית prompt ועיבוד AI
        prompt = build_prompt(messages, memory)
        if not prompt:
            print("אין ידיעות חדשות — לא שולח דוח")
            return

        print("מעבד עם AI...")
        news_digest = await process_with_ai(prompt)

        # עדכון זכרון
        for m in messages:
            if not already_seen(memory, m["text"]):
                add_to_memory(memory, m["text"])
        save_memory(memory)

        # הרכבת הדוח הסופי
        now_he = datetime.now().strftime("%d/%m/%Y %H:%M")
        full_report = f"📋 *דוח חדשות — {now_he}*\n\n{news_digest}"

        # שליחה
        print("שולח דוח...")
        await send_report(tg, full_report)
        print("✅ דוח נשלח בהצלחה!")

if __name__ == "__main__":
    asyncio.run(main())
