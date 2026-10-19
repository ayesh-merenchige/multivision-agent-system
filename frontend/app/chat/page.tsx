"use client";

import { useEffect, useRef, useState } from "react";
import { Plus, Send, Square } from "lucide-react";
import ChatMessage, { type UIMessage } from "@/components/chat/ChatMessage";
import {
  API_URL,
  getHistory,
  getOrder,
  listSessions,
  newSession,
  sendChat,
  type Order,
  type SessionSummary,
} from "@/lib/api";

const EXAMPLES = [
  "What products do you sell?",
  "How much is Smart Hub X1?",
  "I want to order 3 Smart Hub X1.",
];

let idCounter = 0;
const nextId = () => `m-${++idCounter}`;

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // --- session bootstrap ----------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let sid = localStorage.getItem("mv-session_id");
      if (sid) {
        // Validate it still exists on the backend.
        try {
          await getHistory(sid);
        } catch {
          sid = "";
        }
      }
      if (!sid) {
        const created = await newSession();
        sid = created.session_id;
      }
      if (cancelled) return;
      localStorage.setItem("mv-session_id", sid);
      setSessionId(sid);
      await refreshSessions();
      await loadHistory(sid);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshSessions() {
    try {
      setSessions(await listSessions());
    } catch {
      /* ignore */
    }
  }

  async function loadHistory(sid: string) {
    try {
      const hist = await getHistory(sid);
      setMessages(
        hist.messages.map((m) => ({
          id: nextId(),
          role: m.role,
          content: m.content,
          agent: m.agent,
          order: null,
        }))
      );
    } catch {
      /* ignore */
    }
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    });
  }

  useEffect(scrollToBottom, [messages, sending, streaming]);

  async function handleNewChat() {
    const created = await newSession();
    localStorage.setItem("mv-session_id", created.session_id);
    setSessionId(created.session_id);
    setMessages([]);
    await refreshSessions();
    inputRef.current?.focus();
  }

  async function handleSelectSession(sid: string) {
    if (sid === sessionId) return;
    localStorage.setItem("mv-session_id", sid);
    setSessionId(sid);
    setMessages([]);
    await loadHistory(sid);
  }

  // --- sending (with SSE streaming) ---------------------------------------
  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || sending) return;
    setInput("");
    setSending(true);

    const userMsg: UIMessage = { id: nextId(), role: "user", content };
    const assistantId = nextId();
    const assistantMsg: UIMessage = { id: assistantId, role: "assistant", content: "" };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    try {
      const order = await streamChat(sessionId, content, (token) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + token } : m
          )
        );
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, order: order ?? m.order } : m))
      );
      await refreshSessions();
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: "Sorry — I couldn't reach the assistant right now. Please try again.",
              }
            : m
        )
      );
    } finally {
      setSending(false);
      setStreaming(false);
    }
  }

  function streamChat(
    sid: string,
    message: string,
    onToken: (token: string) => void
  ): Promise<Order | null> {
    return new Promise((resolve, reject) => {
      fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, message }),
      })
        .then(async (res) => {
          if (!res.ok || !res.body) throw new Error(`stream failed (${res.status})`);
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let order: Order | null = null;

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split("\n\n");
            buffer = events.pop() ?? "";
            for (const evt of events) {
              const line = evt.split("\n").find((l) => l.startsWith("data:"));
              if (!line) continue;
              const data = JSON.parse(line.slice(5));
              if (data.type === "token") {
                onToken(data.token);
              } else if (data.type === "done") {
                if (data.order_id) {
                  order = await getOrder(data.order_id).catch(() => null);
                }
              }
            }
          }
          resolve(order);
        })
        .catch(reject);
    });
  }

  return (
    <div className="flex h-[calc(100vh-7.5rem)] gap-4">
      {/* Sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-sm md:flex dark:border-slate-800 dark:bg-slate-900">
        <button
          onClick={handleNewChat}
          className="mb-3 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
        >
          <Plus size={16} /> New chat
        </button>
        <div className="flex-1 space-y-1 overflow-y-auto">
          {sessions.map((s) => (
            <button
              key={s.session_id}
              onClick={() => handleSelectSession(s.session_id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                s.session_id === sessionId
                  ? "bg-brand-50 font-medium text-brand-700 dark:bg-brand-900/40 dark:text-brand-200"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <span className="block truncate">{s.title}</span>
              <span className="block text-[11px] text-slate-400">{s.message_count} messages</span>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="px-3 py-2 text-xs text-slate-400">No past sessions yet.</p>
          )}
        </div>
      </aside>

      {/* Main chat */}
      <div className="flex min-w-0 flex-1 flex-col rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 dark:border-slate-800">
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-dot" />
            Assistant online
          </div>
          <button
            onClick={handleNewChat}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 md:hidden dark:hover:bg-slate-800"
          >
            <Plus size={15} /> New
          </button>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-4 py-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-orange-600 text-white">
                <Send size={22} />
              </div>
              <h2 className="mt-4 text-lg font-semibold">How can I help you today?</h2>
              <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                Ask about our products, prices, or company — or place an order in plain language.
              </p>
              <div className="mt-5 flex max-w-md flex-wrap justify-center gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => handleSend(ex)}
                    className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-sm text-slate-600 transition hover:border-brand-300 hover:text-brand-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:text-brand-200"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => (
            <ChatMessage key={m.id} message={m} />
          ))}
          {streaming && (
            <div className="flex items-center gap-2 pl-11 text-sm text-slate-400">
              <span className="flex gap-1">
                <span className="h-2 w-2 rounded-full bg-brand-400 animate-pulse-dot" />
                <span className="h-2 w-2 rounded-full bg-brand-400 animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
                <span className="h-2 w-2 rounded-full bg-brand-400 animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
              </span>
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="border-t border-slate-100 p-3 dark:border-slate-800">
          <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-800">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              placeholder="Ask about products, prices, or place an order…"
              className="max-h-32 flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] outline-none placeholder:text-slate-400"
            />
            <button
              onClick={() => handleSend()}
              disabled={sending || !input.trim()}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 text-white shadow-sm transition hover:opacity-90 disabled:opacity-40"
              aria-label="Send"
            >
              {streaming ? <Square size={15} /> : <Send size={16} />}
            </button>
          </div>
          <p className="mt-1.5 px-1 text-[11px] text-slate-400">
            Powered by LangGraph · Gemini. Press Enter to send, Shift+Enter for a new line.
          </p>
        </div>
      </div>
    </div>
  );
}
