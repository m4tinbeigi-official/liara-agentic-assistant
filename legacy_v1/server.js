const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const port = Number(process.env.PORT || 3000);
const publicDir = path.join(__dirname, 'public');

const sources = {
  deploy: { title: 'استقرار برنامه در لیارا', url: 'https://docs.liara.ir/paas/', label: 'مستندات PaaS لیارا' },
  node: { title: 'راهنمای Node.js', url: 'https://docs.liara.ir/paas/nodejs/', label: 'راهنمای Node.js' },
  docker: { title: 'استقرار با Docker', url: 'https://docs.liara.ir/paas/docker/', label: 'راهنمای Docker' },
  database: { title: 'پایگاه داده‌های لیارا', url: 'https://docs.liara.ir/paas/databases/', label: 'مستندات دیتابیس' }
};

function detectPlatform(text) {
  const value = text.toLowerCase();
  if (/laravel|php|artisan/.test(value)) return 'php';
  if (/django|gunicorn|python|uvicorn/.test(value)) return 'python';
  if (/next|react|node|npm|yarn|pnpm|express/.test(value)) return 'node';
  if (/docker|dockerfile/.test(value)) return 'docker';
  return 'node';
}

function configFor(platform, appName, appPort) {
  const config = { app: appName, platform, port: appPort, build: { location: 'iran' } };
  return JSON.stringify(config, null, 2);
}

function diagnose(log) {
  const value = log.toLowerCase();
  const platform = detectPlatform(log);
  if (/eaddrinuse|address already in use|listen eacces|port/.test(value)) {
    return {
      tool: 'تحلیل‌گر لاگ: خطای پورت شناسایی شد',
      title: 'برنامه روی پورت مورد انتظار لیارا گوش نمی‌دهد',
      answer: 'لیارا شماره پورت را از متغیر محیطی `PORT` در اختیار برنامه قرار می‌دهد. پورت را به عدد ثابت محدود نکنید و برنامه را روی `0.0.0.0` اجرا کنید.',
      steps: ['در کد Node.js از `process.env.PORT || 3000` استفاده کنید.', 'مطمئن شوید سرور با میزبان `0.0.0.0` اجرا می‌شود.', 'هنگام deploy، پورت برنامه را با `--port` مشخص کنید.'],
      code: "const port = process.env.PORT || 3000;\napp.listen(port, '0.0.0.0');\n\n# سپس اجرا کنید\nliara deploy --app=<APP_NAME> --port=3000",
      source: sources.node
    };
  }
  if (/database|postgres|mongodb|econnrefused|timeout|authentication failed/.test(value)) {
    return {
      tool: 'تحلیل‌گر لاگ: اتصال دیتابیس بررسی شد',
      title: 'اتصال به پایگاه داده برقرار نشده است',
      answer: 'رشته اتصال را از بخش تنظیمات سرویس دیتابیس در پنل لیارا دریافت کنید و آن را به‌صورت متغیر محیطی تعریف کنید. اطلاعات محرمانه را داخل مخزن یا `liara.json` قرار ندهید.',
      steps: ['متغیر `DATABASE_URL` را در تنظیمات برنامه تعریف کنید.', 'مطمئن شوید نام کاربری، گذرواژه، میزبان و پورت URI صحیح است.', 'برای اتصال امن، تنظیمات SSL درایور را مطابق نوع دیتابیس بررسی کنید.'],
      code: 'DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DB"\n\n# بررسی لاگ‌ها\nliara logs -f --app=<APP_NAME>',
      source: sources.database
    };
  }
  if (/oom|out of memory|killed|heap/.test(value)) {
    return { tool: 'تحلیل‌گر لاگ: مصرف حافظه بررسی شد', title: 'احتمال کمبود حافظه در زمان build یا runtime', answer: 'لاگ نشان می‌دهد پردازش با محدودیت حافظه مواجه شده است. وابستگی‌های غیرضروری را حذف کنید، build را بهینه کنید و در صورت نیاز منابع برنامه را در پنل افزایش دهید.', steps: ['source mapهای production را غیرفعال کنید.', 'در Docker از multi-stage build استفاده کنید.', 'مصرف حافظه را از لاگ‌های برنامه بررسی کنید.'], code: 'NODE_OPTIONS=--max-old-space-size=512\nliara logs -f --app=<APP_NAME>', source: sources.deploy };
  }
  return { tool: 'تحلیل‌گر لاگ: الگوی قطعی یافت نشد', title: 'برای عیب‌یابی دقیق‌تر، لاگ کامل لازم است', answer: `پلتفرم احتمالی پروژه شما ${platform} است. ۳۰ تا ۵۰ خط قبل و بعد از نخستین خط خطا را ارسال کنید تا عامل بتواند ریشه مشکل را جدا کند.`, steps: ['اولین خط شامل Error یا Exception را پیدا کنید.', 'نام سرویس و مرحله رخداد (build یا runtime) را مشخص کنید.', 'لاگ را بدون توکن و رمز عبور ارسال کنید.'], code: 'liara logs -f --app=<APP_NAME>', source: sources.deploy };
}

function chat(message) {
  const value = message.toLowerCase();
  if (/error|exception|failed|خطا|کرش|لاگ|eaddr|timeout/.test(value)) return diagnose(message);
  const platform = detectPlatform(message);
  if (/liara\.json|کانفیگ|config|dockerfile|پیکربندی|deploy|استقرار/.test(value)) {
    const selected = platform === 'docker' ? sources.docker : platform === 'node' ? sources.node : sources.deploy;
    return { tool: 'سازنده کانفیگ: پلتفرم تشخیص داده شد', title: `پیکربندی آماده برای ${platform === 'node' ? 'Node.js' : platform}`, answer: 'این فایل پایه برای استقرار روی PaaS لیارا آماده است. نام برنامه را با نامی که در پنل ساخته‌اید جایگزین کنید.', steps: ['فایل را در ریشه پروژه با نام `liara.json` قرار دهید.', 'نام برنامه را با نام اپلیکیشن در پنل یکی کنید.', 'با CLI لیارا دستور deploy را اجرا کنید.'], code: configFor(platform, 'my-liara-app', 3000) + '\n\nliara deploy --app=my-liara-app --port=3000', source: selected };
  }
  if (/دیتابیس|database|postgres|mongo|redis/.test(value)) {
    return { tool: 'جست‌وجوی ترکیبی: سرویس دیتابیس', title: 'اتصال امن برنامه به دیتابیس لیارا', answer: 'سرویس دیتابیس را از پنل لیارا ایجاد کنید، سپس URI اتصال را در متغیرهای محیطی برنامه بگذارید. هیچ‌وقت URI را در کد یا Git ثبت نکنید.', steps: ['دیتابیس مناسب را از پنل ایجاد کنید.', 'اطلاعات اتصال را از صفحه سرویس دریافت کنید.', 'متغیر محیطی را در تنظیمات برنامه تعریف و در کد مصرف کنید.'], code: 'const connectionString = process.env.DATABASE_URL;\n\nliara logs -f --app=<APP_NAME>', source: sources.database };
  }
  return { tool: 'جست‌وجوی ترکیبی: مستندات رسمی', title: 'مسیر سریع شروع استقرار در لیارا', answer: 'برای استقرار، ابتدا برنامه را در پنل لیارا بسازید، CLI را نصب و وارد حساب شوید، سپس از ریشه پروژه فرمان deploy را اجرا کنید. پلتفرم و پورت باید با برنامه شما هم‌خوان باشد.', steps: ['یک برنامه PaaS در پنل لیارا بسازید.', 'با API Token وارد Liara CLI شوید.', 'از ریشه پروژه فرمان deploy را اجرا کنید و لاگ build را بررسی کنید.'], code: 'liara login --api-token=<TOKEN>\nliara deploy --app=<APP_NAME> --port=3000\nliara logs -f --app=<APP_NAME>', source: sources.deploy };
}

function sendJson(res, status, data) { res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(data)); }

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (req.method === 'GET' && url.pathname === '/health') return sendJson(res, 200, { status: 'ok' });
  if (req.method === 'GET' && url.pathname === '/api/v1/docs/search') {
    const query = url.searchParams.get('q') || '';
    return sendJson(res, 200, { query, results: Object.values(sources) });
  }
  if (req.method === 'POST' && ['/api/v1/agent/chat', '/api/v1/agent/diagnose', '/api/v1/agent/generate-config'].includes(url.pathname)) {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const input = JSON.parse(body || '{}');
        const result = url.pathname.endsWith('/diagnose') ? diagnose(input.log || input.message || '') : url.pathname.endsWith('/generate-config') ? chat(`config ${input.platform || 'node'}`) : chat(input.message || '');
        sendJson(res, 200, result);
      } catch { sendJson(res, 400, { error: 'بدنه درخواست JSON معتبر نیست.' }); }
    });
    return;
  }
  const fileName = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
  const filePath = path.join(publicDir, fileName);
  if (!filePath.startsWith(publicDir) || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) { res.writeHead(404); return res.end('Not found'); }
  const type = filePath.endsWith('.css') ? 'text/css' : filePath.endsWith('.js') ? 'application/javascript' : 'text/html';
  res.writeHead(200, { 'Content-Type': `${type}; charset=utf-8` });
  fs.createReadStream(filePath).pipe(res);
});

server.listen(port, '0.0.0.0', () => console.log(`Liara Copilot running on port ${port}`));
