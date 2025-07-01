import os
import secrets
from supabase import create_client, Client
from datetime import datetime
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- Gemini Key Caching ---
_list_keys_cache = {"data": None, "ts": 0}
_LIST_KEYS_TTL = 300  # seconds

def list_keys():
    now = time.time()
    if _list_keys_cache["data"] is not None and now - _list_keys_cache["ts"] < _LIST_KEYS_TTL:
        return _list_keys_cache["data"]
    res = supabase.table("projects").select("id, name, region, api_key, model_name, active").execute()
    data = res.data if hasattr(res, 'data') else []
    _list_keys_cache["data"] = data
    _list_keys_cache["ts"] = now
    return data

def add_key(name, region, api_key, model_name):
    return supabase.table("projects").insert({"name": name, "region": region, "api_key": api_key, "model_name": model_name, "active": True}).execute()

def remove_key(key_id):
    return supabase.table("projects").delete().eq("id", key_id).execute()

# --- User API Key Caching ---
_list_user_keys_cache = {"data": None, "ts": 0}
_LIST_USER_KEYS_TTL = 300  # seconds

def list_user_api_keys():
    now = time.time()
    if _list_user_keys_cache["data"] is not None and now - _list_user_keys_cache["ts"] < _LIST_USER_KEYS_TTL:
        return _list_user_keys_cache["data"]
    res = supabase.table("user_api_keys").select("id, user_label, key, active, created_at").execute()
    data = res.data if hasattr(res, 'data') else []
    _list_user_keys_cache["data"] = data
    _list_user_keys_cache["ts"] = now
    return data

def create_user_api_key(user_label):
    api_key = secrets.token_urlsafe(32)
    now = datetime.utcnow().isoformat()
    res = supabase.table("user_api_keys").insert({
        "key": api_key,
        "user_label": user_label,
        "active": True,
        "created_at": now
    }).execute()
    return api_key if res else None

def revoke_user_api_key(key_id):
    result = supabase.table("user_api_keys").update({"active": False}).eq("id", key_id).execute()
    _list_user_keys_cache["data"] = None
    _list_user_keys_cache["ts"] = 0
    return result

def is_valid_user_api_key(api_key):
    res = supabase.table("user_api_keys").select("id").eq("key", api_key).eq("active", True).execute()
    return bool(res.data)

# --- Admin Management ---
def list_admins():
    res = supabase.table("users").select("telegram_id").eq("is_admin", True).execute()
    return [r["telegram_id"] for r in res.data] if hasattr(res, 'data') else []

def add_admin(telegram_id):
    # Upsert user as admin
    return supabase.table("users").upsert({"telegram_id": telegram_id, "is_admin": True}).execute()

def remove_admin(telegram_id):
    return supabase.table("users").update({"is_admin": False}).eq("telegram_id", telegram_id).execute()

def is_admin(telegram_id):
    res = supabase.table("users").select("id").eq("telegram_id", telegram_id).eq("is_admin", True).execute()
    return bool(res.data)

# TODO: Add functions for key management, user management, usage logging 

def create_bot(name, token, base_prompt=None):
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    # Create a user API key for this bot
    api_key = secrets.token_urlsafe(32)
    api_key_row = supabase.table("user_api_keys").insert({
        "key": api_key,
        "user_label": name,
        "active": True,
        "created_at": now
    }).execute()
    api_key_id = api_key_row.data[0]["id"] if hasattr(api_key_row, 'data') and api_key_row.data else None
    # Create the bot
    res = supabase.table("bots").insert({
        "name": name,
        "token": token,
        "status": "active",
        "base_prompt": base_prompt,
        "api_key_id": api_key_id,
        "created_at": now
    }).execute()
    return res, api_key

def list_bots():
    res = supabase.table("bots").select("id, name, status, created_at, base_prompt").execute()
    return res.data if hasattr(res, 'data') else []

def get_bot_api_key_and_prompt(bot_id):
    # Returns (api_key, base_prompt)
    bot = supabase.table("bots").select("api_key_id, base_prompt").eq("id", bot_id).single().execute()
    if not hasattr(bot, 'data') or not bot.data:
        return None, None
    api_key_id = bot.data["api_key_id"]
    base_prompt = bot.data["base_prompt"]
    key_row = supabase.table("user_api_keys").select("key").eq("id", api_key_id).single().execute()
    api_key = key_row.data["key"] if hasattr(key_row, 'data') and key_row.data else None
    return api_key, base_prompt 