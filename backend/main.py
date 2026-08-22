"""
Liara Agentic Copilot — main.py
FastAPI server with 5 API endpoints + static frontend serving.
"""
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Header, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from agent import run_agent_stream
from tools import (
    generate_liara_json,
    generate_dockerfile,
    diagnose_error,
    SUPPORTED_PLATFORMS,
)
from vector_store import search_docs, RAG_ENABLED, has_docs


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if RAG_ENABLED and not has_docs():
        print("[startup] RAG enabled but index is empty — running local ingestion...")
        try:
            from ingest import run_ingestion
            run_ingestion()
        except Exception as e:
            print(f"[startup] ingestion failed: {e}")
    print("[startup] Liara Copilot backend ready")
    yield
    print("[shutdown] Liara Copilot backend stopping")


app = FastAPI(
    title="Liara Agentic Copilot",
    version="2.0.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_origins == "*" else [o.strip() for o in _cors_origins.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ─── Basic in-memory rate limiting (per-IP sliding window) ─────────────────

RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW_S = int(os.getenv("RATE_LIMIT_WINDOW_S", "60"))
_rate_buckets: dict[str, deque] = defaultdict(deque)


def _is_rate_limited(client_ip: str) -> bool:
    now = time.monotonic()
    bucket = _rate_buckets[client_ip]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_S:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        return True
    bucket.append(now)
    return False


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        if _is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED", "message_fa": "تعداد درخواست‌ها بیش از حد مجاز است. کمی صبر کنید."}},
            )
    return await call_next(request)


# ─── Request/Response Models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="پیام کاربر")
    session_id: str = Field(default="default", max_length=128, description="شناسه نشست")

class DiagnoseRequest(BaseModel):
    log: str = Field(..., min_length=1, description="متن لاگ خطا")

class GenerateConfigRequest(BaseModel):
    platform: str = Field(..., description="نوع پلتفرم")
    app_name: str = Field(default="my-app", description="نام برنامه")
    port: Optional[int] = Field(default=None, description="پورت برنامه")

class ErrorResponse(BaseModel):
    error: dict = Field(..., example={"code": "VALIDATION_ERROR", "message_fa": "..."})


# ─── SSE Headers ─────────────────────────────────────────────────────────────

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Liara Copilot Backend is running."}


@app.post("/api/v1/agent/chat")
async def chat_endpoint(req: ChatRequest, authorization: str = Header(None)):
    try:
        api_token = ""
        if authorization and authorization.startswith("Bearer "):
            api_token = authorization.split(" ", 1)[1]

        return StreamingResponse(
            run_agent_stream(req.message, api_token, req.session_id),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/v1/agent/diagnose")
async def diagnose_endpoint(req: DiagnoseRequest):
    """تحلیل لاگ خطا و پیشنهاد راهکار."""
    try:
        result = diagnose_error(req.log)
        return {"result": result}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "DIAGNOSE_ERROR", "message_fa": str(e)}},
        )


@app.post("/api/v1/agent/generate-config")
async def generate_config_endpoint(req: GenerateConfigRequest):
    """تولید فایل liara.json."""
    if req.platform.lower() not in SUPPORTED_PLATFORMS:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "UNSUPPORTED_PLATFORM",
                    "message_fa": f"پلتفرم '{req.platform}' پشتیبانی نمی‌شود. معتبر: {', '.join(SUPPORTED_PLATFORMS)}",
                }
            },
        )
    try:
        config_result = generate_liara_json(req.platform, req.app_name, req.port)
        dockerfile_result = generate_dockerfile(req.platform, req.port)
        return {"config": config_result, "dockerfile": dockerfile_result}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "CONFIG_ERROR", "message_fa": str(e)}},
        )


@app.get("/api/v1/docs/search")
async def docs_search_endpoint(
    q: str = Query(None, description="عبارت جستجو"),
    platform: Optional[str] = Query(None, description="فیلتر پلتفرم"),
):
    """جستجوی مستقیم مستندات لیارا."""
    if not q or not q.strip():
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "EMPTY_QUERY", "message_fa": "پارامتر q الزامی است."}},
        )
    try:
        results = search_docs(q.strip(), top_k=5)
        return {"query": q, "results": results or "موردی یافت نشد."}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "RETRIEVAL_UNAVAILABLE", "message_fa": str(e)}},
        )


# ─── Static Frontend ────────────────────────────────────────────────────────

if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ─── Dev Runner ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
