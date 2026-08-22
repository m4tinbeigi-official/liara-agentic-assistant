"""
Liara Agentic Copilot — tools.py
Production tools: config generator, log diagnoser, app status, dockerfile
generator, CLI command validator.
"""
import difflib
import json
import re
import shlex
import httpx
from typing import Optional


# ─── Platform Templates ──────────────────────────────────────────────────────

PLATFORM_TEMPLATES = {
    "node": {"platform": "node", "port": 3000, "build": {"location": "iran"}},
    "next": {"platform": "node", "port": 3000, "build": {"location": "iran"}},
    "react": {"platform": "node", "port": 3000, "build": {"location": "iran"}},
    "vue": {"platform": "node", "port": 3000, "build": {"location": "iran"}},
    "angular": {"platform": "node", "port": 4200, "build": {"location": "iran"}},
    "python": {"platform": "docker", "port": 8000, "build": {"location": "iran"}},
    "django": {"platform": "docker", "port": 8000, "build": {"location": "iran"}},
    "flask": {"platform": "docker", "port": 5000, "build": {"location": "iran"}},
    "fastapi": {"platform": "docker", "port": 8000, "build": {"location": "iran"}},
    "laravel": {"platform": "laravel", "port": 80, "build": {"location": "iran"}},
    "php": {"platform": "php", "port": 80, "build": {"location": "iran"}},
    "docker": {"platform": "docker", "port": 3000, "build": {"location": "iran"}},
    "go": {"platform": "docker", "port": 8080, "build": {"location": "iran"}},
    "dotnet": {"platform": "docker", "port": 5000, "build": {"location": "iran"}},
    "static": {"platform": "static", "port": 80},
}

SUPPORTED_PLATFORMS = sorted(PLATFORM_TEMPLATES.keys())


def generate_liara_json(platform: str, app_name: str = "my-app", port: Optional[int] = None) -> str:
    """Generates a valid liara.json configuration."""
    platform = platform.lower().strip()
    if platform not in PLATFORM_TEMPLATES:
        return (
            f"پلتفرم `{platform}` پشتیبانی نمی‌شود.\n"
            f"پلتفرم‌های معتبر: {', '.join(SUPPORTED_PLATFORMS)}"
        )

    config = {"app": app_name, **PLATFORM_TEMPLATES[platform]}
    if port:
        config["port"] = port

    code = f"```json\n{json.dumps(config, indent=2, ensure_ascii=False)}\n```"
    instructions = (
        f"\n\n**راهنما:**\n"
        f"1. فایل `liara.json` را در ریشه پروژه قرار دهید.\n"
        f"2. اجرا کنید: `liara deploy --app={app_name}`\n"
        f"\n[مستندات استقرار {platform}](https://docs.liara.ir/paas/{platform}/)"
    )
    return code + instructions


def generate_dockerfile(platform: str, port: Optional[int] = None) -> str:
    """Generates a Dockerfile template for given platform."""
    platform = platform.lower().strip()
    templates = {
        "node": (
            "FROM node:20-alpine\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm ci --prefer-offline\n"
            "COPY . .\n"
            "RUN npm run build 2>/dev/null || true\n"
            "EXPOSE {port}\n"
            'CMD ["node", "server.js"]'
        ),
        "python": (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["python", "app.py"]'
        ),
        "django": (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "RUN python manage.py collectstatic --noinput 2>/dev/null || true\n"
            "EXPOSE {port}\n"
            'CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:{port}"]'
        ),
        "fastapi": (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]'
        ),
        "flask": (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:{port}"]'
        ),
        "go": (
            "FROM golang:1.22-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY go.* ./\n"
            "RUN go mod download\n"
            "COPY . .\n"
            "RUN CGO_ENABLED=0 go build -o main .\n\n"
            "FROM alpine:3.19\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/main .\n"
            "EXPOSE {port}\n"
            'CMD ["./main"]'
        ),
    }

    p = port or PLATFORM_TEMPLATES.get(platform, {}).get("port", 3000)
    template = templates.get(platform, templates.get("node"))
    dockerfile = template.format(port=p)

    return f"```dockerfile\n{dockerfile}\n```\n\n[مستندات Dockerfile لیارا](https://docs.liara.ir/paas/docker/)"


# ─── Error Diagnosis Patterns ────────────────────────────────────────────────

ERROR_PATTERNS = [
    {
        "keywords": ["eaddrinuse", "port", "پورت", "address already in use"],
        "title": "خطای Port Binding (EADDRINUSE)",
        "solution": (
            "لیارا پورت را از متغیر محیطی `PORT` تزریق می‌کند.\n\n"
            "**رفع:**\n"
            "```js\n"
            "const port = process.env.PORT || 3000;\n"
            "app.listen(port, '0.0.0.0');\n"
            "```\n"
            "و در `liara.json` پورت را تنظیم کنید:\n"
            "```json\n"
            '{ "port": 3000 }\n'
            "```\n"
            "[مستندات پورت لیارا](https://docs.liara.ir/paas/nodejs/)"
        ),
    },
    {
        "keywords": ["econnrefused", "connection refused", "database", "دیتابیس", "mongo", "postgres", "mysql", "redis"],
        "title": "خطای اتصال دیتابیس",
        "solution": (
            "**رفع:**\n"
            "1. URI اتصال را از پنل لیارا > دیتابیس‌ها کپی کنید\n"
            "2. به عنوان متغیر محیطی تعریف کنید:\n"
            "```\n"
            "DATABASE_URL=postgresql://user:pass@host:5432/db\n"
            "```\n"
            "3. در برنامه از `process.env.DATABASE_URL` استفاده کنید\n\n"
            "[مستندات دیتابیس لیارا](https://docs.liara.ir/databases/)"
        ),
    },
    {
        "keywords": ["oom", "killed", "out of memory", "memory", "حافظه", "heap"],
        "title": "خطای کمبود حافظه (OOM Killed)",
        "solution": (
            "**رفع:**\n"
            "1. پلن برنامه را در پنل لیارا ارتقا دهید (حداقل ۵۱۲MB)\n"
            "2. برای Node.js حد حافظه تنظیم کنید:\n"
            "```\n"
            "NODE_OPTIONS=--max-old-space-size=512\n"
            "```\n"
            "3. فرآیندهای اضافی (مثل build داخل container) را حذف کنید\n\n"
            "[مستندات منابع لیارا](https://docs.liara.ir/paas/)"
        ),
    },
    {
        "keywords": ["module not found", "cannot find module", "no module named", "import error", "modulenotfounderror"],
        "title": "خطای ماژول/پکیج یافت نشد",
        "solution": (
            "**رفع:**\n"
            "1. مطمئن شوید فایل `package.json` یا `requirements.txt` کامل است\n"
            "2. برای Node.js: `npm install` و push مجدد `package-lock.json`\n"
            "3. برای Python: اطمینان از وجود همه پکیج‌ها در `requirements.txt`\n"
            "4. اگر از Docker استفاده می‌کنید، بررسی کنید `COPY` قبل از `RUN install` باشد\n\n"
            "[مستندات عیب‌یابی لیارا](https://docs.liara.ir/)"
        ),
    },
    {
        "keywords": ["permission denied", "read-only", "erofs", "فقط خواندنی", "readonly"],
        "title": "خطای فایل‌سیستم فقط خواندنی",
        "solution": (
            "**رفع:**\n"
            "فایل‌سیستم لیارا فقط خواندنی است. برای نوشتن فایل:\n"
            "1. یک دیسک پایدار در `liara.json` تعریف کنید:\n"
            "```json\n"
            '{ "disks": [{ "name": "data", "mountTo": "/app/uploads" }] }\n'
            "```\n"
            "2. در پنل لیارا دیسک را بسازید\n"
            "3. فقط در مسیر mount شده بنویسید\n\n"
            "[مستندات دیسک لیارا](https://docs.liara.ir/paas/disks/)"
        ),
    },
    {
        "keywords": ["timeout", "504", "gateway timeout", "تایم‌اوت"],
        "title": "خطای Timeout / Gateway Timeout",
        "solution": (
            "**رفع:**\n"
            "1. بررسی کنید برنامه به پورت درست گوش می‌دهد\n"
            "2. زمان پاسخ‌دهی healthcheck را بررسی کنید\n"
            "3. اگر build طولانی دارید، timeout بیلد را افزایش دهید\n"
            "4. برای عملیات سنگین از Job/Queue استفاده کنید\n\n"
            "[مستندات لیارا](https://docs.liara.ir/)"
        ),
    },
]


def diagnose_error(log: str) -> str:
    """Analyzes an error log and returns diagnosis + remediation."""
    log_lower = log.lower()

    matches = []
    for pattern in ERROR_PATTERNS:
        if any(kw in log_lower for kw in pattern["keywords"]):
            matches.append(pattern)

    if not matches:
        return (
            "**تحلیل لاگ:**\n\n"
            "الگوی شناخته‌شده‌ای در لاگ یافت نشد. پیشنهادات عمومی:\n"
            "1. لاگ‌های کامل را با `liara logs -f --app=<APP>` بررسی کنید\n"
            "2. `liara.json` را اعتبارسنجی کنید\n"
            "3. اطمینان حاصل کنید پورت صحیح تنظیم شده\n\n"
            "[مستندات عیب‌یابی](https://docs.liara.ir/)"
        )

    parts = ["**تحلیل لاگ:**\n"]
    for m in matches:
        parts.append(f"### {m['title']}\n{m['solution']}\n")

    return "\n".join(parts)


# ─── Liara Cloud API ─────────────────────────────────────────────────────────

async def get_liara_app_status(api_token: str, app_name: str = "my-app") -> str:
    """Fetches app status from Liara API (async)."""
    if not api_token or api_token in ("null", "", "__TOKEN__"):
        return (
            "**برای دریافت وضعیت برنامه، توکن API لیارا لازم است.**\n\n"
            "توکن را از پنل لیارا > تنظیمات حساب دریافت کنید و "
            "در هدر `Authorization: Bearer <TOKEN>` ارسال نمایید.\n\n"
            "[دریافت توکن](https://console.liara.ir/)"
        )

    url = f"https://api.iran.liara.ir/v1/projects/{app_name}"
    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            project = data.get("project", {})
            status = project.get("status", "نامشخص")
            plan = project.get("planID", "نامشخص")
            return (
                f"**وضعیت برنامه `{app_name}`:**\n\n"
                f"| فیلد | مقدار |\n|---|---|\n"
                f"| وضعیت | {status} |\n"
                f"| پلن | {plan} |\n"
            )
        elif response.status_code == 404:
            return f"برنامه `{app_name}` یافت نشد. نام را بررسی کنید."
        elif response.status_code == 401:
            return "توکن نامعتبر است. لطفاً توکن جدید از پنل لیارا دریافت کنید."
        else:
            return f"خطای API لیارا: {response.status_code}"

    except httpx.TimeoutException:
        return "خطا: ارتباط با API لیارا قطع شد (Timeout). دوباره تلاش کنید."
    except Exception as e:
        return f"خطا در اتصال به API لیارا: {e}"


# ─── Liara CLI Command Validator ─────────────────────────────────────────────
# spec.md promises the copilot "دستورات CLI را اعتبارسنجی می‌کند" (validates
# CLI commands) before the user runs them. This closes that gap: catches
# unknown subcommands, missing required flags, and malformed values (bad
# app-name syntax, out-of-range ports) offline, without shelling out to the
# real `liara` binary.

APP_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

CLI_COMMANDS = {
    "login": {
        "desc": "ورود به حساب کاربری لیارا",
        "required": [],
        "flags": {"api-token": True, "email": True, "password": True, "region": True},
    },
    "logout": {"desc": "خروج از حساب کاربری", "required": [], "flags": {}},
    "whoami": {"desc": "نمایش حساب کاربری فعال", "required": [], "flags": {}},
    "init": {"desc": "ساخت liara.json تعاملی", "required": [], "flags": {"platform": True}},
    "deploy": {
        "desc": "استقرار پروژه فعلی",
        "required": ["app"],
        "flags": {
            "app": True, "port": True, "platform": True, "image-file": True,
            "message": True, "disable-detect": False, "no-cache": False, "debug": False,
        },
    },
    "logs": {
        "desc": "مشاهده لاگ‌های برنامه",
        "required": ["app"],
        "flags": {"app": True, "follow": False, "since": True, "timestamp": False},
    },
    "shell": {"desc": "اتصال ترمینال به کانتینر برنامه", "required": ["app"], "flags": {"app": True}},
    "app:list": {"desc": "لیست برنامه‌ها", "required": [], "flags": {}},
    "app:start": {"desc": "روشن کردن برنامه", "required": ["app"], "flags": {"app": True}},
    "app:stop": {"desc": "خاموش کردن برنامه", "required": ["app"], "flags": {"app": True}},
    "app:restart": {"desc": "ری‌استارت برنامه", "required": ["app"], "flags": {"app": True}},
    "app:remove": {"desc": "حذف برنامه", "required": ["app"], "flags": {"app": True}},
    "disk:list": {"desc": "لیست دیسک‌های یک برنامه", "required": ["app"], "flags": {"app": True}},
    "disk:create": {"desc": "ساخت دیسک پایدار", "required": ["app", "name", "mount-to"], "flags": {"app": True, "name": True, "mount-to": True}},
    "env:list": {"desc": "لیست متغیرهای محیطی", "required": ["app"], "flags": {"app": True}},
    "env:set": {"desc": "تنظیم متغیر محیطی", "required": ["app"], "flags": {"app": True, "variables": True}},
}

# CLI-flag aliases → canonical Liara subcommand, so a user pasting
# "liara app --list" or similar near-misses still gets routed sanely.
_KNOWN_SUBCOMMANDS = sorted(CLI_COMMANDS.keys())


def _closest_subcommand(name: str) -> Optional[str]:
    matches = difflib.get_close_matches(name, _KNOWN_SUBCOMMANDS, n=1, cutoff=0.5)
    return matches[0] if matches else None


def validate_cli_command(command: str) -> str:
    """Statically validates a `liara ...` CLI command string and reports
    unknown subcommands, missing required flags, and malformed values."""
    command = (command or "").strip()
    if not command:
        return "دستوری برای بررسی وارد نشده است."

    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return f"❌ **دستور قابل تجزیه نیست:** نحو نامعتبر (`{e}`). گیومه‌ها را بررسی کنید."

    if not tokens:
        return "دستوری برای بررسی وارد نشده است."

    if tokens[0] != "liara":
        return (
            f"❌ **این یک دستور Liara CLI نیست.** دستورات باید با `liara` شروع شوند "
            f"(دریافت شد: `{tokens[0]}`)."
        )

    if len(tokens) < 2:
        return "❌ **زیردستور مشخص نشده.** مثال: `liara deploy --app=my-app`"

    subcommand = tokens[1]
    spec = CLI_COMMANDS.get(subcommand)
    if spec is None:
        suggestion = _closest_subcommand(subcommand)
        hint = f" آیا منظور شما `liara {suggestion}` بود؟" if suggestion else ""
        return (
            f"❌ **زیردستور ناشناخته:** `{subcommand}`.{hint}\n\n"
            f"زیردستورهای معتبر: {', '.join(f'`{c}`' for c in _KNOWN_SUBCOMMANDS)}"
        )

    # Parse `--flag=value` / `--flag value` / boolean `--flag`
    parsed_flags: dict[str, Optional[str]] = {}
    i = 2
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("--"):
            if "=" in tok:
                key, value = tok[2:].split("=", 1)
            else:
                key = tok[2:]
                takes_value = spec["flags"].get(key, False)
                if takes_value and i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                    value = tokens[i + 1]
                    i += 1
                else:
                    value = None
            parsed_flags[key] = value
        elif tok.startswith("-") and len(tok) == 2:
            # short flags (e.g. -f for --follow) — accepted but not deeply validated
            parsed_flags[tok[1:]] = None
        i += 1

    errors, warnings = [], []

    unknown_flags = [f for f in parsed_flags if f not in spec["flags"] and len(f) > 1]
    for f in unknown_flags:
        suggestion = difflib.get_close_matches(f, list(spec["flags"].keys()), n=1, cutoff=0.5)
        hint = f" (آیا `--{suggestion[0]}` بود؟)" if suggestion else ""
        warnings.append(f"فلگ `--{f}` برای `{subcommand}` شناخته‌شده نیست.{hint}")

    missing = [f for f in spec["required"] if f not in parsed_flags]
    for f in missing:
        errors.append(f"فلگ الزامی `--{f}` وارد نشده است.")

    if "app" in parsed_flags and parsed_flags["app"]:
        if not APP_NAME_RE.match(parsed_flags["app"]):
            errors.append(
                f"نام برنامه `{parsed_flags['app']}` نامعتبر است. فقط حروف کوچک، عدد و خط تیره مجاز است "
                f"(نمی‌تواند با خط تیره شروع/پایان یابد)."
            )

    if "port" in parsed_flags and parsed_flags["port"]:
        port_val = parsed_flags["port"]
        if not port_val.isdigit() or not (1 <= int(port_val) <= 65535):
            errors.append(f"پورت `{port_val}` نامعتبر است. باید عددی بین ۱ تا ۶۵۵۳۵ باشد.")

    if errors:
        body = "\n".join(f"- {e}" for e in errors)
        result = f"❌ **دستور نامعتبر است** (`liara {subcommand}`):\n\n{body}"
    else:
        result = f"✅ **دستور معتبر است:** `{command}`\n\n*{spec['desc']}*"

    if warnings:
        result += "\n\n⚠️ " + "\n\n⚠️ ".join(warnings)

    return result
