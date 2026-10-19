"use client";

import { Bot, User } from "lucide-react";
import Markdown from "@/components/Markdown";
import OrderCard from "./OrderCard";
import type { Order, TraceEntry } from "@/lib/api";

export interface UIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string | null;
  order?: Order | null;
  trace?: TraceEntry[];
}

const AGENT_BADGE: Record<string, { label: string; cls: string }> = {
  catalog: { label: "Catalog Agent", cls: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
  chat: { label: "Chat Agent", cls: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
  order: { label: "Order Agent", cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300" },
  supervisor: { label: "Supervisor", cls: "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300" },
};

export default function ChatMessage({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";
  const badge = message.agent ? AGENT_BADGE[message.agent] : undefined;

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""} animate-fade-in`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200"
            : "bg-gradient-to-br from-brand-500 to-orange-600 text-white"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className={`max-w-[80%] ${isUser ? "items-end text-right" : ""}`}>
        {badge && (
          <span className={`mb-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${badge.cls}`}>
            via {badge.label}
          </span>
        )}
        <div
          className={`rounded-2xl px-4 py-2.5 shadow-sm ${
            isUser
              ? "rounded-tr-sm bg-brand-600 text-white"
              : "rounded-tl-sm border border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          }`}
        >
          {isUser ? (
            <p className="text-[15px]">{message.content}</p>
          ) : (
            <Markdown text={message.content} />
          )}
          {message.order && <OrderCard order={message.order} />}
        </div>
      </div>
    </div>
  );
}
