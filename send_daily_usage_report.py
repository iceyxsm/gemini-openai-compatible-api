import os
import requests
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_yesterday_stats():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    start = datetime(yesterday.year, yesterday.month, yesterday.day)
    end = datetime(today.year, today.month, today.day)
    # Query usage_logs for yesterday
    res = supabase.table("usage_logs").select("user_id, project_id, prompt_tokens, response_tokens, total_tokens, timestamp").gte("timestamp", start.isoformat()).lt("timestamp", end.isoformat()).execute()
    logs = res.data if hasattr(res, 'data') else []
    total_requests = len(logs)
    total_tokens = sum(l.get("total_tokens", 0) for l in logs)
    # Top users
    user_counts = {}
    for l in logs:
        uid = l.get("user_id")
        user_counts[uid] = user_counts.get(uid, 0) + 1
    top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    # Top bots/projects
    bot_counts = {}
    for l in logs:
        pid = l.get("project_id")
        bot_counts[pid] = bot_counts.get(pid, 0) + 1
    top_bots = sorted(bot_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    return total_requests, total_tokens, top_users, top_bots

def get_user_label(user_id):
    if not user_id:
        return "Unknown"
    res = supabase.table("users").select("user_label, telegram_id").eq("id", user_id).single().execute()
    if hasattr(res, 'data') and res.data:
        return res.data.get("user_label") or str(res.data.get("telegram_id"))
    return str(user_id)

def get_bot_label(project_id):
    if not project_id:
        return "Unknown"
    res = supabase.table("projects").select("name").eq("id", project_id).single().execute()
    if hasattr(res, 'data') and res.data:
        return res.data.get("name")
    return str(project_id)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_TELEGRAM_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def main():
    total_requests, total_tokens, top_users, top_bots = get_yesterday_stats()
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    msg = f"<b>[Daily Usage Report: {yesterday}]</b>\n"
    msg += f"- Total requests: {total_requests}\n"
    msg += f"- Total tokens used: {total_tokens}\n"
    msg += "- Top users:\n"
    for uid, count in top_users:
        label = get_user_label(uid)
        msg += f"  - {label}: {count} requests\n"
    msg += "- Top bots/projects:\n"
    for pid, count in top_bots:
        label = get_bot_label(pid)
        msg += f"  - {label}: {count} requests\n"
    send_telegram_message(msg)

if __name__ == "__main__":
    main() 