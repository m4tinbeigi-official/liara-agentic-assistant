const conversation = document.querySelector('#conversation');
const form = document.querySelector('#composer');
const message = document.querySelector('#message');

function escapeHtml(value) { const node = document.createElement('div'); node.textContent = value; return node.innerHTML; }
function copyCode(button) { navigator.clipboard.writeText(button.previousElementSibling.textContent); button.textContent = 'کپی شد'; setTimeout(() => { button.textContent = 'کپی'; }, 1600); }
function renderResult(result) {
  const steps = result.steps.map((step, index) => `<li><b>${index + 1}</b>${escapeHtml(step)}</li>`).join('');
  const item = document.createElement('article');
  item.className = 'answer';
  item.innerHTML = `<div class="agent-line"><span class="tiny-orb">✦</span><span>${escapeHtml(result.tool)}</span></div><h3>${escapeHtml(result.title)}</h3><p>${escapeHtml(result.answer)}</p><ol>${steps}</ol><div class="code"><button onclick="copyCode(this)">کپی</button><pre>${escapeHtml(result.code)}</pre></div><a class="citation" href="${result.source.url}" target="_blank" rel="noreferrer">↗ ${escapeHtml(result.source.label)} <span>${escapeHtml(result.source.title)}</span></a>`;
  conversation.append(item); conversation.scrollTop = conversation.scrollHeight;
}
async function submit(text) {
  if (!text.trim()) return;
  const question = document.createElement('article'); question.className = 'question'; question.textContent = text; conversation.append(question);
  const loading = document.createElement('div'); loading.className = 'working'; loading.innerHTML = '<i></i> عامل در حال تحلیل درخواست و جست‌وجوی مستندات...'; conversation.append(loading); conversation.scrollTop = conversation.scrollHeight;
  try { const response = await fetch('/api/v1/agent/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) }); renderResult(await response.json()); } catch { renderResult({ tool: 'خطای اتصال', title: 'ارتباط با عامل برقرار نشد', answer: 'لطفاً اتصال برنامه را بررسی و دوباره تلاش کنید.', steps: ['صفحه را تازه‌سازی کنید.'], code: 'GET /health', source: { url: 'https://docs.liara.ir/', label: 'مستندات رسمی', title: 'لیارا' } }); } finally { loading.remove(); }
}
form.addEventListener('submit', event => { event.preventDefault(); const text = message.value; message.value = ''; submit(text); });
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => submit(button.dataset.prompt)));
message.addEventListener('input', () => { message.style.height = 'auto'; message.style.height = `${Math.min(message.scrollHeight, 130)}px`; });
