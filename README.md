<!-- DevSponsors Badges -->
<p align="center">
  <a href="https://devsponsors.github.io"><img src="https://img.shields.io/badge/DevSponsors-Verified_OSS-6366f1?style=for-the-badge&logo=github" alt="DevSponsors Verified"></a>
  <a href="https://devsponsors.github.io"><img src="https://img.shields.io/badge/Sponsor-DevSponsors_Hub-emerald?style=for-the-badge&logo=github-sponsors" alt="DevSponsors Sponsor"></a>
  <a href="https://devsponsors.github.io/mediakit.html"><img src="https://img.shields.io/badge/Infrastructure-DevSponsors_Cloud-ec4899?style=for-the-badge&logo=server" alt="DevSponsors Cloud"></a>
</p>

# Liara Agentic Copilot

دستیار هوشمند عاملی (Agentic AI Copilot) برای پلتفرم ابری لیارا — مبتنی بر LLM با tool calling، RAG روی مستندات و رابط چت فارسی.

## قابلیت‌ها

- **چت هوشمند با LLM**: پاسخ‌دهی فارسی با ارجاع به مستندات لیارا
- **تحلیل خطا**: تشخیص خودکار خطاهای Port، Database، OOM، Module و Permission
- **ساخت کانفیگ**: تولید `liara.json` و `Dockerfile` برای ۱۵+ پلتفرم
- **بررسی وضعیت**: اتصال به API لیارا با توکن کاربر
- **RAG (اختیاری)**: جستجوی برداری روی مستندات لیارا با `RAG_ENABLED=1`

## API Endpoints

| Method | Path | توضیح |
|--------|------|-------|
| GET | `/health` | بررسی سلامت سرور |
| POST | `/api/v1/agent/chat` | چت SSE با عامل هوشمند |
| POST | `/api/v1/agent/diagnose` | تحلیل لاگ خطا |
| POST | `/api/v1/agent/generate-config` | تولید liara.json + Dockerfile |
| GET | `/api/v1/docs/search?q=...` | جستجوی مستندات |

## اجرای محلی

```bash
# 1. کپی تنظیمات
cp backend/.env.example backend/.env
# API key خود را در .env وارد کنید

# 2. نصب وابستگی‌های بک‌اند
cd backend
pip install -r requirements.txt

# 3. اجرای سرور
python main.py
# → http://localhost:3000

# 4. (اختیاری) بیلد فرانت‌اند
cd ../frontend
npm install
npm run build
# کپی out/ به backend/static/
```

## استقرار روی لیارا

1. یک برنامه Docker در پنل لیارا بسازید
2. متغیرهای محیطی را تنظیم کنید:
   - `LLM_API_KEY`: کلید API سرویس هوش مصنوعی
   - `LLM_BASE_URL`: آدرس سرویس (مثلاً `https://api.avalai.ir/v1`)
   - `LLM_MODEL`: نام مدل (مثلاً `gpt-4o-mini`)
3. دیپلوی:
```bash
liara deploy --app=<APP_NAME> --port=3000
```

## استک فنی

- **Backend**: FastAPI + OpenAI SDK + LangGraph-free agentic loop
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS + react-markdown + Prism
- **Vector DB**: Qdrant (local, persistent disk)
- **Embedding**: fastembed (ONNX, بدون PyTorch)

## منابع

- [مستندات رسمی لیارا](https://docs.liara.ir/)
- [مخزن مستندات لیارا](https://github.com/liara-cloud/docs)
