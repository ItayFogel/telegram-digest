"""
סקריפט חד-פעמי ליצירת session string לטלגרם.
הרץ אותו פעם אחת על המחשב שלך, שמור את הפלט כ-Secret ב-GitHub.
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("הכנס API_ID: ").strip())
API_HASH = input("הכנס API_HASH: ").strip()


async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_string = client.session.save()
        print("\n" + "="*60)
        print("✅ SESSION STRING (שמור אותו כ-Secret בשם TELEGRAM_SESSION):")
        print("="*60)
        print(session_string)
        print("="*60)

        me = await client.get_me()
        print(f"\nמחובר כ: {me.first_name} (ID: {me.id})")
        print(f"שמור את ה-ID הזה כ-Secret בשם MY_TELEGRAM_ID: {me.id}")


asyncio.run(main())
