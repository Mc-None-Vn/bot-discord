from fastapi.responses import PlainTextResponse, JSONResponse, Response
from fastapi import FastAPI, Header, HTTPException, Path, Query
from upstash_redis import Redis
from data import data
import os, json

# ================== CONFIG ==================

RATE_LIMIT = 5
RATE_WINDOW = 1
API_KEY_ENV = "API_Key"
COOLDOWN = 60
TEMPBAN = 3600

# ================== INIT ==================

app = FastAPI()
redis = Redis.from_env()
API_KEY = os.getenv(API_KEY_ENV)

if not API_KEY:
    raise RuntimeError("API_Key not set")
API_KEYS = {k.strip() for k in API_KEY.split("|")}
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# ================== UTILS ==================

def verify_api_key(x_api_key: str | None):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")

async def check_limit(user_id: str):
    if await redis.exists(f"cd2:{user_id}") == 1:
        return 2
    if await redis.exists(f"cd1:{user_id}") == 1:
        key = f"rl:{user_id}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, RATE_WINDOW)
        if count > RATE_LIMIT:
            await redis.setex(f"cd2:{user_id}", TEMPBAN, 1)
            await redis.delete(key)
            return 2
        return 1
    key = f"rl:{user_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, RATE_WINDOW)
    if count > RATE_LIMIT:
        await redis.delete(key)
        await redis.setex(f"cd1:{user_id}", COOLDOWN, 1)
        return 1
    return 0

def safe_path(file_path: str):
    if ".." in file_path or file_path.startswith("/"):
        raise HTTPException(403, "Access denied")
    abs_path = os.path.abspath(os.path.join(ROOT_DIR, file_path))
    if not abs_path.startswith(ROOT_DIR):
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(abs_path):
        raise HTTPException(404, "File not found")
    return abs_path

# ================== ROUTE ==================

@app.get("/{file_path:path}")
async def get_static_file(file_path: str = Path(...), id: str = Query(...), x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    status = await check_limit(id)

    # ===== TEMPBAN =====
    if status == 2:
        raise HTTPException(status_code=403, detail="Temporarily banned", headers={"X-Type": "tempban"})

    # ===== COOLDOWN =====
    if status == 1:
        return Response(status_code=429, headers={"X-Type": "cooldown"})

    # ===== FILE HANDLING =====
    abs_path = safe_path(file_path)
    ext = os.path.splitext(abs_path)[1].lower()

    if ext == ".json":
        with open(abs_path, "r", encoding="utf-8") as f:
            return JSONResponse(json.load(f))

    if ext in {".txt", ".md", ".log"}:
        with open(abs_path, "r", encoding="utf-8") as f:
            return PlainTextResponse(data(f.read()))

    with open(abs_path, "rb") as f:
        return Response(content=f.read(), media_type="application/octet-stream")
