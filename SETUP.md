# 📋 מדריך התקנה — מתמצת חדשות טלגרם

## שלב 1 — קבלת מפתחות Telegram API

1. היכנס ל-[my.telegram.org](https://my.telegram.org)
2. לחץ על **API development tools**
3. מלא שם אפליקציה (לדוגמה: `my_digest`) ולחץ **Create**
4. תקבל `api_id` ו-`api_hash` — שמור אותם

---

## שלב 2 — קבלת מפתח מזג אוויר (חינם)

1. הירשם ב-[openweathermap.org](https://openweathermap.org/api)
2. עבור ל-**My API Keys**
3. העתק את המפתח החינמי

---

## שלב 3 — יצירת Session String (פעם אחת בלבד)

על המחשב שלך:

```bash
pip install telethon
python create_session.py
```

תתבקש להזין:
- `API_ID` ו-`API_HASH` מהשלב הקודם
- מספר טלפון + קוד SMS שיגיע לטלפון

בסוף תקבל:
- **SESSION STRING** — מחרוזת ארוכה
- **MY_TELEGRAM_ID** — מספר ה-ID שלך

---

## שלב 4 — יצירת Repository ב-GitHub

1. צור repository חדש בשם `telegram-digest` (פרטי ✅)
2. העלה את הקבצים:
   - `digest.py`
   - `create_session.py`
   - `requirements.txt`
   - `.github/workflows/digest.yml`

---

## שלב 5 — הגדרת Secrets ב-GitHub

ב-Repository שלך: **Settings → Secrets and variables → Actions → New repository secret**

הוסף את הסודות הבאים:

| שם | ערך |
|---|---|
| `TELEGRAM_API_ID` | המספר מ-my.telegram.org |
| `TELEGRAM_API_HASH` | המחרוזת מ-my.telegram.org |
| `TELEGRAM_SESSION` | ה-Session String הארוך |
| `MY_TELEGRAM_ID` | מספר ה-ID שלך |
| `ANTHROPIC_API_KEY` | המפתח מ-console.anthropic.com |
| `OPENWEATHER_API_KEY` | המפתח מ-openweathermap.org |

---

## שלב 6 — בדיקה ידנית

ב-GitHub: **Actions → Telegram News Digest → Run workflow**

אם הכל תקין — תקבל הודעה בטלגרם תוך דקה! ✅

---

## תזמון

המערכת תשלח אוטומטית בכל יום:
- **07:00** שעון ישראל
- **20:00** שעון ישראל

---

## פתרון בעיות

**לא מגיעה הודעה?**
- בדוק ב-Actions שהריצה הצליחה (ירוק ✅)
- אם יש שגיאה אדומה — לחץ עליה ותראה את הלוג המלא

**Session פג?**
- הרץ מחדש את `create_session.py` ועדכן את ה-Secret
