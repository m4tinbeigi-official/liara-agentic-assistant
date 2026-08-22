import { test, expect } from '@playwright/test';

// ─── Capability: health endpoint ───────────────────────────────────────────
test.describe('Health Check', () => {
  test('GET /health returns ok', async ({ request }) => {
    const res = await request.get('http://localhost:3000/health');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });
});

// ─── Capability: agent-workflow ─────────────────────────────────────────────
test.describe('Agent Workflow — intent routing', () => {
  test('routes config intent → generate_config', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/v1/agent/chat', {
      data: { message: 'یک liara.json برای node بساز' },
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.status()).toBe(200);
    const text = await res.text();
    // SSE stream باید شامل tool call مربوط به config builder باشد
    expect(text).toContain('generate_config');
  });

  test('routes error/log intent → diagnose_error', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/v1/agent/chat', {
      data: { message: 'Error: listen EADDRINUSE :::3000' },
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.status()).toBe(200);
    const text = await res.text();
    expect(text).toContain('diagnose_error');
  });

  test('handles empty message with 400', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/v1/agent/chat', {
      data: { message: '' },
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.status()).toBe(400);
  });
});

// ─── Capability: config builder (tools.py) ──────────────────────────────────
test.describe('Config Builder', () => {
  test('generates valid liara.json content in stream', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/v1/agent/chat', {
      data: { message: 'config برای django بساز' },
      headers: { 'Content-Type': 'application/json' },
    });
    const text = await res.text();
    // خروجی باید حاوی docker یا platform باشد
    expect(text.toLowerCase()).toContain('docker');
    expect(text).toContain('8000');
  });
});

// ─── Capability: cloud-ops (no token → graceful message) ────────────────────
test.describe('Cloud Ops', () => {
  test('returns graceful message when no token provided', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/v1/agent/chat', {
      data: { message: 'وضعیت برنامه my-app را بگو' },
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.status()).toBe(200);
    const text = await res.text();
    // باید پیام راهنما برای توکن نداشتن بیاید
    expect(text).toContain('توکن');
  });
});

// ─── Capability: interactive-ui (frontend) ──────────────────────────────────
test.describe('Interactive UI', () => {
  test('page loads and shows welcome text', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'لیارا' })).toBeVisible();
  });

  test('user can type and submit a message', async ({ page }) => {
    await page.goto('/');
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('چطور روی لیارا دیپلوی کنم؟');
    await page.keyboard.press('Enter');
    // باید spinner یا پاسخ ظاهر شود
    await expect(page.locator('text=در حال پاسخگویی')).toBeVisible({ timeout: 5000 })
      .catch(() => {
        // اگر خیلی سریع جواب داد spinner نمی‌ماند — پاسخ خود را چک کن
        return expect(page.locator('[class*="assistant"], [class*="answer"]').first()).toBeVisible({ timeout: 8000 });
      });
  });

  test('tool badge appears for config request', async ({ page }) => {
    await page.goto('/');
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('liara.json برای node بساز');
    await page.keyboard.press('Enter');
    // tool badge باید بعد از پاسخ ظاهر شود (تکست نمایشی generate_liara_json است)
    await expect(page.locator('text=generate_liara_json')).toBeVisible({ timeout: 15000 });
  });
});
