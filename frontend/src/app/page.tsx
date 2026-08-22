"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

/* ─── Types ──────────────────────────────────────────────────────────────── */

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  tools: string[];
};

/* ─── Suggestions ────────────────────────────────────────────────────────── */

const SUGGESTIONS = [
  { icon: "🚀", label: "استقرار Node.js", prompt: "چطور یک برنامه Node.js روی لیارا deploy کنم؟" },
  { icon: "🔍", label: "تحلیل خطای پورت", prompt: "Error: listen EADDRINUSE :::3000" },
  { icon: "⚙️", label: "ساخت liara.json", prompt: "یک liara.json برای Django بساز" },
  { icon: "📊", label: "وضعیت برنامه", prompt: "وضعیت برنامه my-app را بررسی کن" },
  { icon: "🐳", label: "ساخت Dockerfile", prompt: "یک Dockerfile برای پروژه FastAPI بساز" },
  { icon: "❓", label: "راهنمای دیسک", prompt: "چطور دیسک پایدار در لیارا تنظیم کنم؟" },
  { icon: "✅", label: "بررسی دستور CLI", prompt: "liara deploy --app=My_App --port=99999 معتبر است؟" },
];

/* ─── Copy Button Component ──────────────────────────────────────────────── */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* fallback for non-secure contexts */
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button onClick={handleCopy} className={`copy-btn ${copied ? "copied" : ""}`}>
      {copied ? "✓ کپی شد" : "کپی"}
    </button>
  );
}

/* ─── Markdown Renderer ──────────────────────────────────────────────────── */

function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const codeString = String(children).replace(/\n$/, "");

          if (match) {
            return (
              <div className="code-block-wrapper">
                <div className="code-header">
                  <span>{match[1]}</span>
                  <CopyButton text={codeString} />
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="pre"
                  customStyle={{
                    margin: 0,
                    padding: "1rem",
                    background: "#0f172a",
                    fontSize: "0.8125rem",
                  }}
                >
                  {codeString}
                </SyntaxHighlighter>
              </div>
            );
          }

          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
        a({ href, children }) {
          return (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

/* ─── Tool Badge ─────────────────────────────────────────────────────────── */

const TOOL_LABELS: Record<string, { icon: string; label: string }> = {
  search_docs: { icon: "🔎", label: "جستجوی مستندات" },
  generate_config: { icon: "⚙️", label: "generate_liara_json" },
  generate_dockerfile: { icon: "🐳", label: "ساخت Dockerfile" },
  diagnose_error: { icon: "🩺", label: "تحلیل خطا" },
  get_app_status: { icon: "📊", label: "بررسی وضعیت" },
  validate_cli_command: { icon: "✅", label: "اعتبارسنجی دستور CLI" },
};

function ToolBadge({ name }: { name: string }) {
  const info = TOOL_LABELS[name] || { icon: "⚙", label: name };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs bg-violet-900/40 text-violet-300 border border-violet-700/40 px-2.5 py-1 rounded-full animate-fade-in">
      <span>{info.icon}</span>
      <span>{info.label}</span>
      <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
    </span>
  );
}

/* ─── Main Component ─────────────────────────────────────────────────────── */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const msgIdCounter = useRef(0);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  /* ─── SSE Parser ─────────────────────────────────────────────────────── */

  const parseSSEChunk = useCallback(
    (buffer: string): { events: { type: string; [k: string]: string }[]; remainder: string } => {
      const events: { type: string; [k: string]: string }[] = [];
      const lines = buffer.split("\n");
      let remainder = "";

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("data: ")) {
          const raw = line.slice(6).trim();
          if (!raw) continue;
          try {
            events.push(JSON.parse(raw));
          } catch {
            if (i === lines.length - 1) remainder = line;
          }
        }
      }
      return { events, remainder };
    },
    []
  );

  /* ─── Submit ─────────────────────────────────────────────────────────── */

  const submit = async (text: string) => {
    const msg = text.trim();
    if (!msg || isTyping) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userId = `msg-${++msgIdCounter.current}`;
    const assistantId = `msg-${++msgIdCounter.current}`;

    setMessages((prev) => [
      ...prev,
      { id: userId, role: "user", content: msg, tools: [] },
      { id: assistantId, role: "assistant", content: "", tools: [] },
    ]);
    setIsTyping(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
      const res = await fetch(`${apiUrl}/api/v1/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const { events, remainder } = parseSSEChunk(buffer);
        buffer = remainder;

        for (const event of events) {
          if (event.type === "done") break;
          setMessages((prev) => {
            const updated = [...prev];
            const last = { ...updated[updated.length - 1] };
            if (event.type === "tool" && event.name && !last.tools.includes(event.name)) {
              last.tools = [...last.tools, event.name];
            } else if (event.type === "content") {
              last.content += event.text;
            }
            updated[updated.length - 1] = last;
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          id: assistantId,
          role: "assistant",
          content: `⚠️ متأسفانه ارتباط با سرور برقرار نشد. لطفاً دوباره تلاش کنید.\n\nجزئیات فنی: ${
            err instanceof Error ? err.message : "خطای ناشناخته"
          }`,
          tools: [],
        };
        return updated;
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submit(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  /* ─── UI ─────────────────────────────────────────────────────────────── */

  return (
    <main className="app-shell flex flex-col h-screen bg-slate-950 text-slate-200">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 sm:px-6 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md shrink-0">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center font-bold text-white text-sm shadow-lg shadow-violet-600/30 pulse-glow">
          L
        </div>
        <div>
          <h1 className="font-semibold text-sm text-slate-100">Liara Agentic Copilot</h1>
          <p className="text-[11px] text-slate-500">پاسخ فنی · عیب‌یابی خطا · ساخت کانفیگ و Dockerfile</p>
        </div>
        <span className="ms-auto flex items-center gap-1.5 text-xs text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          آنلاین
        </span>
      </header>

      {/* Conversation */}
      <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-6 space-y-4" role="log" aria-live="polite">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center animate-fade-in">
            <div className="float-slow w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600/20 to-purple-700/20 border border-violet-500/30 flex items-center justify-center text-3xl">
              ✦
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">
                سلام! من کوپایلوت لیارا هستم
              </h2>
              <p className="text-sm text-slate-500 mt-1.5 max-w-sm mx-auto leading-relaxed">
                پیام خطا رو بفرستید، یک کانفیگ بخواهید، یا هر سوالی درباره استقرار روی لیارا دارید بپرسید
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-2xl">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.prompt}
                  onClick={() => submit(s.prompt)}
                  className="suggestion-card flex items-center gap-3 text-right p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 hover:border-violet-500/60 hover:bg-slate-700/60 transition-all duration-200 text-sm text-slate-300 hover:text-slate-100 group"
                >
                  <span className="text-lg group-hover:scale-110 transition-transform shrink-0">
                    {s.icon}
                  </span>
                  <span>{s.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end animate-slide-right" : "justify-start animate-slide-left"}`}
          >
            <div className="max-w-[90%] sm:max-w-[80%] lg:max-w-[70%] space-y-2">
              {/* Tool badges */}
              {msg.role === "assistant" && msg.tools.length > 0 && (
                <div className="flex gap-2 flex-wrap">
                  {msg.tools.map((t) => (
                    <ToolBadge key={t} name={t} />
                  ))}
                </div>
              )}
              {/* Bubble */}
              <div
                data-testid={msg.role === "user" ? "user-message" : "assistant-message"}
                className={`${
                  msg.role === "user" ? "user-message" : "assistant-message"
                } px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-gradient-to-br from-violet-600 to-purple-700 text-white rounded-br-sm shadow-lg shadow-violet-600/20"
                    : "bg-slate-800/80 text-slate-200 rounded-bl-sm border border-slate-700/60"
                } ${msg.role === "assistant" && msg.content.startsWith("⚠️") ? "error-message" : ""}`}
              >
                {msg.content ? (
                  msg.role === "assistant" ? (
                    <div className="prose-chat" dir="auto">
                      <MarkdownContent content={msg.content} />
                    </div>
                  ) : (
                    <div dir="auto" style={{ whiteSpace: "pre-wrap" }}>
                      {msg.content}
                    </div>
                  )
                ) : msg.role === "assistant" && isTyping ? (
                  <span className="flex gap-2 items-center text-slate-400">
                    <span className="flex gap-1 items-center">
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce [animation-delay:0ms]" />
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce [animation-delay:150ms]" />
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce [animation-delay:300ms]" />
                    </span>
                    <span className="typing-status text-xs">در حال نوشتن پاسخ…</span>
                  </span>
                ) : null}
              </div>
            </div>
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <form onSubmit={handleSubmit} className="shrink-0 px-3 sm:px-6 pb-4">
        <div className="flex items-end gap-2 bg-slate-800/80 border border-slate-700/60 focus-within:border-violet-500/60 focus-within:shadow-lg focus-within:shadow-violet-600/10 rounded-2xl px-4 py-3 transition-all duration-200">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="سؤال، پیام خطا یا نیاز استقرارتان را بنویسید…"
            disabled={isTyping}
            dir="auto"
            className="composer-textarea flex-1 bg-transparent resize-none outline-none text-sm text-slate-200 placeholder:text-slate-500 max-h-36"
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-purple-700 hover:from-violet-500 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 flex items-center justify-center transition-all duration-200 shrink-0 text-white shadow-lg shadow-violet-600/20 disabled:shadow-none"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
        <p className="text-center text-[11px] text-slate-600 mt-2">
          پاسخ‌ها بر پایه مستندات رسمی لیارا تولید می‌شوند و ممکن است نیاز به بازبینی داشته باشند
        </p>
      </form>
    </main>
  );
}
