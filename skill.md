---
name: liara-agentic-copilot
description: مهارت‌های تخصصی عامل هوشمند برای توسعه، استقرار، عیب‌یابی و پیکربندی اپلیکیشن‌ها روی پلتفرم ابری لیارا (Liara Cloud)
---

# مهارت تخصصی توسعه و پشتیبانی پلتفرم لیارا

## ۱. ساختار مرجع فایل liara.json
```json
{
  "app": "my-cool-app",
  "port": 3000,
  "platform": "node",
  "build": {
    "location": "iran"
  },
  "disks": [
    {
      "name": "data-volume",
      "mountTo": "/app/uploads"
    }
  ]
}
```

## ۲. دستورالعمل استاندارد استقرار روی لیارا
- لاگین با توکن: `liara login --api-token=<TOKEN>`
- استقرار پروژه فعلی: `liara deploy --app=<APP_NAME> --port=<PORT>`
- مشاهده لاگ‌های زنده: `liara logs -f --app=<APP_NAME>`

## ۳. الگوهای عیب‌یابی خطاهای رایج
- **خطای Port Binding:** بررسی تعریف متغیر `PORT` در برنامه و تنظیم دقیق در `liara.json`.
- **خطای دیسک‌های فقط خواندنی (Read-only Filesystem):** انتقال مسیر فایل‌های ذخیره‌سازی به پوشه مونت‌شده دیسک پایدار.
