import uvicorn
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import uuid
import datetime
import os
import requests
from supabase_client import is_valid_user_api_key, list_keys
import redis
from rq import Queue
import time
import logging

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = redis.from_url(REDIS_URL)
queue = Queue("gemini_requests", connection=redis_conn)

def log_usage(user_api_key, gemini_key_id, prompt_tokens, completion_tokens, total_tokens):
    pass  # TODO: Implement usage logging

def count_tokens(text):
    return len(text.split())

def openai_error(message, code="invalid_request_error", status=400):
    return JSONResponse(status_code=status, content={
        "error": {
            "message": message,
            "type": code,
            "param": None,
            "code": code
        }
    })

app = FastAPI()

RATE_LIMIT_PER_REGION = int(os.getenv("RATE_LIMIT_PER_REGION", 60))

def current_minute():
    return int(time.time() // 60)

def region_key(region):
    return f"gemini_rate:{region}:{current_minute()}"

def can_send_request(region):
    key = region_key(region)
    count = redis_conn.get(key)
    if count is None:
        redis_conn.set(key, 1, ex=60)
        return True
    elif int(count) < RATE_LIMIT_PER_REGION:
        redis_conn.incr(key)
        return True
    else:
        return False

def gemini_worker(payload, region, api_key, model_name):
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
    logging.warning(f"[DEBUG] Gemini API call: url={url}")
    logging.warning(f"[DEBUG] Payload: {payload}")
    logging.warning(f"[DEBUG] Model: {model_name}")
    logging.warning(f"[DEBUG] API key: {api_key[:6]}{'*' * (len(api_key)-6)}")
    resp = requests.post(url, json=payload, timeout=60)
    logging.warning(f"[DEBUG] Raw Gemini API response: {resp.text}")
    try:
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": {"message": str(e)}}, 500

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return openai_error("Missing or invalid Authorization header", "invalid_api_key", 401)
    user_api_key = authorization.split(" ", 1)[1]
    if not is_valid_user_api_key(user_api_key):
        return openai_error("Invalid API key", "invalid_api_key", 401)

    try:
        body = await request.json()
        messages = body["messages"]
        model = body.get("model", "gemini-1.5-pro")
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("max_tokens", 1024)
    except Exception:
        return openai_error("Malformed request body", status=400)

    gemini_keys = [k for k in list_keys() if k["active"]]
    if not gemini_keys:
        return openai_error("No active Gemini API keys configured", status=500)

    gemini_payload = {
        "contents": [
            {
                "role": m["role"],
                "parts": [{"text": m["content"]}]
            }
            for m in messages if "content" in m
        ]
    }

    gemini_text = None
    used_key_id = None
    last_error = None

    for key in gemini_keys:
        region = key["region"]
        model_name = key.get("model_name", model)
        logging.warning(f"[DEBUG] Using model: {model_name} for region: {region}")
        if can_send_request(region):
            try:
                gemini_data, status_code = gemini_worker(gemini_payload, region, key["api_key"], model_name)
                if status_code == 200:
                    gemini_text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
                    used_key_id = key["id"]
                    break
                elif status_code in (429, 403):
                    last_error = gemini_data.get("error", {}).get("message", "Gemini API error")
                    continue
                else:
                    last_error = gemini_data.get("error", {}).get("message", "Gemini API error")
            except Exception as e:
                last_error = str(e)
                continue
        else:
            job = queue.enqueue(gemini_worker, gemini_payload, region, key["api_key"], model_name)
            result = job.result or job.wait(timeout=65)
            if result:
                gemini_data, status_code = result
                if status_code == 200:
                    gemini_text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
                    used_key_id = key["id"]
                    break
                else:
                    last_error = gemini_data.get("error", {}).get("message", "Gemini API error")

    if gemini_text is None:
        return openai_error(f"Gemini API error: {last_error}", status=500)

    prompt_text = " ".join([m["content"] for m in messages if "content" in m])
    prompt_tokens = count_tokens(prompt_text)
    completion_tokens = count_tokens(gemini_text)
    total_tokens = prompt_tokens + completion_tokens

    log_usage(user_api_key, used_key_id, prompt_tokens, completion_tokens, total_tokens)

    openai_response = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:16]}",
        "object": "chat.completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": gemini_text},
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }
    return openai_response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
