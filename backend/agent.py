"""
Liara Agentic Copilot — agent.py
LLM-powered agentic workflow with tool calling and RAG.
"""
import json
import os
from typing import AsyncGenerator

from openai import AsyncOpenAI
from dotenv import load_dotenv

from vector_store import search_docs
from tools import (
    generate_liara_json,
    generate_dockerfile,
    diagnose_error,
    get_liara_app_status,
    validate_cli_command,
    SUPPORTED_PLATFORMS,
)

load_dotenv()

# ─── LLM Client (lazy — works without key at import time for tests) ──────────

_llm_client = None
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def _get_llm_client() -> AsyncOpenAI:
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "sk-placeholder")
        _llm_client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL", "https://api.avalai.ir/v1"),
        )
    return _llm_client

# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """تو دستیار ارشد هوشمند پلتفرم ابری لیارا (Liara) هستی. نام تو «کوپایلوت لیارا» است.

## قوانین:
1. **همیشه فارسی** پاسخ بده مگر اینکه کاربر انگلیسی بنویسد.
2. **دقیق و مستند** باش — حدس نزن. اگر مطمئن نیستی بگو «مطمئن نیستم».
3. برای هر پاسخ فنی، **لینک مستقیم مستندات لیارا** ضمیمه کن.
4. کدها را در بلوک‌های مارکداون با زبان مشخص بنویس (```json, ```js, ```python, ```dockerfile).
5. از ابزارهای موجود استفاده کن:
   - `search_docs`: جستجو در مستندات لیارا
   - `generate_config`: ساخت فایل liara.json
   - `generate_dockerfile`: ساخت Dockerfile
   - `diagnose_error`: تحلیل لاگ خطا
   - `get_app_status`: بررسی وضعیت برنامه در لیارا
   - `validate_cli_command`: اعتبارسنجی دستور Liara CLI قبل از اجرا
6. پاسخ را ساختاریافته و خوانا با هدینگ و لیست بنویس.
7. اگر کاربر سلام کرد یا سوال عمومی پرسید، خودت را معرفی کن و قابلیت‌هایت را لیست کن.

## دامنه تخصص:
- استقرار (Deploy) انواع پروژه روی لیارا (Node.js, Python, Django, Laravel, Docker, Go, .NET, Static)
- عیب‌یابی خطاهای بیلد و رانتایم
- ساخت فایل‌های liara.json و Dockerfile
- مدیریت دیسک، دامنه، SSL، دیتابیس‌های مدیریت‌شده
- متغیرهای محیطی و تنظیمات پلتفرم
"""

# ─── Tool Definitions (OpenAI function calling format) ───────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "جستجو در مستندات رسمی لیارا برای پاسخ به سوالات فنی",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "عبارت جستجو"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_config",
            "description": "ساخت فایل liara.json برای استقرار پروژه",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": f"نوع پلتفرم: {', '.join(SUPPORTED_PLATFORMS)}",
                    },
                    "app_name": {"type": "string", "description": "نام برنامه در لیارا", "default": "my-app"},
                    "port": {"type": "integer", "description": "پورت برنامه", "default": 3000},
                },
                "required": ["platform"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_dockerfile",
            "description": "ساخت Dockerfile برای استقرار پروژه روی لیارا",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "نوع پلتفرم"},
                    "port": {"type": "integer", "description": "پورت برنامه"},
                },
                "required": ["platform"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_error",
            "description": "تحلیل لاگ خطا و ارائه راهکار اصلاحی",
            "parameters": {
                "type": "object",
                "properties": {
                    "log": {"type": "string", "description": "متن لاگ خطا"},
                },
                "required": ["log"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_app_status",
            "description": "بررسی وضعیت برنامه در پلتفرم لیارا",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "نام برنامه", "default": "my-app"},
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_cli_command",
            "description": "اعتبارسنجی یک دستور Liara CLI (مثل liara deploy --app=...) پیش از اجرا؛ زیردستور، فلگ‌های الزامی، نام برنامه و پورت را بررسی می‌کند",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "دستور کامل CLI، مثلاً 'liara deploy --app=my-app --port=3000'"},
                },
                "required": ["command"],
            },
        },
    },
]


# ─── Tool Executor ───────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict, api_token: str = "") -> str:
    """Execute a tool and return result string."""
    try:
        if name == "search_docs":
            result = search_docs(args.get("query", ""))
            if not result:
                return "موردی در مستندات یافت نشد."
            return result

        elif name == "generate_config":
            return generate_liara_json(
                platform=args.get("platform", "node"),
                app_name=args.get("app_name", "my-app"),
                port=args.get("port"),
            )

        elif name == "generate_dockerfile":
            return generate_dockerfile(
                platform=args.get("platform", "node"),
                port=args.get("port"),
            )

        elif name == "diagnose_error":
            return diagnose_error(args.get("log", ""))

        elif name == "get_app_status":
            return await get_liara_app_status(
                api_token=api_token,
                app_name=args.get("app_name", "my-app"),
            )

        elif name == "validate_cli_command":
            return validate_cli_command(args.get("command", ""))

        else:
            return f"ابزار `{name}` شناخته نشد."

    except Exception as e:
        return f"خطا در اجرای ابزار `{name}`: {e}"


# ─── Conversation Memory ────────────────────────────────────────────────────

_sessions: dict[str, list[dict]] = {}
MAX_HISTORY = 20


def _get_messages(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        _sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return _sessions[session_id]


def _trim_history(messages: list[dict]):
    """Keep system + last MAX_HISTORY messages."""
    if len(messages) > MAX_HISTORY + 1:
        system = messages[0]
        tail = messages[-MAX_HISTORY:]
        messages[:] = [system] + tail


# ─── SSE Streaming Generator ────────────────────────────────────────────────

async def run_agent_stream(
    message: str,
    api_token: str = "",
    session_id: str = "default",
) -> AsyncGenerator[str, None]:
    """
    Main agentic loop with LLM tool-calling and streaming.
    Yields SSE events: tool, content, done.
    """
    messages = _get_messages(session_id)
    messages.append({"role": "user", "content": message})

    # ─── Agentic loop (max 3 tool rounds) ───────────────────────────────
    for _round in range(3):
        try:
            response = await _get_llm_client().chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                stream=True,
            )
        except Exception as e:
            error_msg = f"خطا در ارتباط با سرویس هوش مصنوعی: {e}"
            yield f"data: {json.dumps({'type': 'content', 'text': error_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            messages.append({"role": "assistant", "content": error_msg})
            return

        # ── Collect streaming response ──────────────────────────────
        collected_content = ""
        tool_calls_map: dict[int, dict] = {}  # index -> {id, name, arguments}

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Stream text content
            if delta.content:
                collected_content += delta.content
                yield f"data: {json.dumps({'type': 'content', 'text': delta.content}, ensure_ascii=False)}\n\n"

            # Collect tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name or "" if tc.function else "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_calls_map[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_map[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc.function.arguments

        # ── If no tool calls, we're done ────────────────────────────
        if not tool_calls_map:
            # ── Fallback answer extraction if tool fails or LLM refuses ──
            if not collected_content and len(messages) > 1:
                collected_content = "پاسخی از سمت سرویس دریافت نشد."
            messages.append({"role": "assistant", "content": collected_content})
            break

        # ── Execute tool calls ──────────────────────────────────────
        assistant_msg = {
            "role": "assistant",
            "content": collected_content or None,
            "tool_calls": [],
        }

        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            assistant_msg["tool_calls"].append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            })
        messages.append(assistant_msg)

        for idx in sorted(tool_calls_map.keys()):
            tc = tool_calls_map[idx]
            tool_name = tc["name"]

            # Emit tool event to frontend
            yield f"data: {json.dumps({'type': 'tool', 'name': tool_name}, ensure_ascii=False)}\n\n"

            # Parse arguments
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}

            # Execute
            result = await execute_tool(tool_name, args, api_token)

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        # Loop continues — LLM will synthesize tool results

    _trim_history(messages)
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
