# مستندات معماری، ساختار داده و رابط کاربری (Design Doc)

## ۱. معماری گردش کار چندعاملی (Multi-Agent Workflow Architecture)
```
┌─────────────────────────────────────────────────────────────┐
│                 User Input (Query / Error Log)              │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    Supervisor / Router Agent                │
│       (Intent Classification & Platform Detection)          │
└───┬──────────────────────────┬──────────────────────────┬───┘
    │ Troubleshooting Intent   │ Config Generation        │ Docs Q&A
┌───▼──────────────────────┐ ┌─▼────────────────────────┐ ┌─▼──────────────────────┐
│   Diagnostic Agent       │ │   Config Builder Agent   │ │   Agentic RAG Agent    │
│ (Log & Stacktrace Parser)│ │(liara.json & Dockerfile) │ │  (Hybrid Docs Search)  │
└───┬──────────────────────┘ └─┬────────────────────────┘ └──┬─────────────────────┘
    │                          │                           │
    └──────────────────────────┼───────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                  Synthesis & Verification Layer              │
│       (Adds Deep Links, CLI Snippets & Validations)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Streaming SSE / Markdown
┌──────────────────────────────▼──────────────────────────────┐
│                 Next.js Frontend / Terminal UI              │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. پروتکل عیب‌یابی لاگ (Diagnostic Protocol)
```
Step 1: Parse Error Input (Regex & LLM Entity Extractor)
        ├── Detect Framework (e.g. Next.js, Django, Laravel)
        ├── Detect Error Class (e.g. Port Binding, DB Timeout, OOM, Build Lock)
Step 2: Query Vector DB for matched Troubleshooting Section
Step 3: Generate Remediation Plan
        ├── Plain Persian explanation
        ├── Exact line-by-line configuration fix
        └── Liara CLI command for verification
```

---

## ۳. هویت بصری و دیزاین سیستم رابط کاربری
- **رنگ‌های اصلی:** بنفش سازمانی لیارا (`#7928CA` / `#6D28D9`)، خاکستری مات دارک (`#0F172A`, `#1E293B`).
- **کامپوننت‌های فرانت‌اند:**
  - `CodeSnippetViewer`: با قابلیت هایلایت سینتکس و دکمه One-Click Copy.
  - `ActionPill`: نشان‌دهنده ابزار در حال اجرا (مثلاً «در حال جستجوی مستندات پستگرس...»).
  - `DirectCitationBadge`: تگ‌های کلیک‌خور برای ارجاع به مستندات مرجع.
