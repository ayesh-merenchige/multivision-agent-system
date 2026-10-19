import Link from "next/link";
import {
  ArrowRight,
  Bot,
  BarChart3,
  ShoppingCart,
  Sparkles,
  Settings2,
} from "lucide-react";

const FEATURES = [
  {
    icon: ShoppingCart,
    title: "Conversational Commerce",
    desc: "Ask about products, prices, and your company — and place orders entirely in natural language.",
  },
  {
    icon: Bot,
    title: "Multi-Agent AI",
    desc: "A supervisor routes each request to a specialized catalog, chat, or order agent powered by Gemini.",
  },
  {
    icon: BarChart3,
    title: "Live Dashboard",
    desc: "Monitor agent activity, orders, revenue, and KPIs with auto-refreshing charts and logs.",
  },
  {
    icon: Settings2,
    title: "Full CRUD Admin",
    desc: "Manage company details, products, and pricing tiers — persisted to JSON with validation.",
  },
];

export default function Home() {
  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-brand-600 via-brand-500 to-orange-600 px-6 py-16 text-white shadow-xl dark:border-slate-800 sm:px-12 sm:py-24">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-24 -left-10 h-64 w-64 rounded-full bg-orange-300/20 blur-2xl" />
        <div className="relative">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur">
            <Sparkles size={14} /> Powered by LangGraph + Gemini
          </span>
          <h1 className="mt-5 max-w-2xl text-4xl font-bold leading-tight sm:text-5xl">
            One assistant.
            <br />
            Every division.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-brand-50">
            Multivisions is a multi-agent business assistant that chats with
            customers, places orders, monitors itself, and lets you manage the
            whole catalog — all from a single, production-ready platform.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-brand-700 shadow-lg transition hover:bg-brand-50"
            >
              Start Chatting <ArrowRight size={16} />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mt-10">
        <h2 className="text-center text-2xl font-bold">Everything a modern business needs</h2>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                <f.icon size={20} />
              </div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats strip */}
      <section className="mt-10 grid gap-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:grid-cols-3">
        {[
          ["3", "Specialized agents"],
          ["10", "Products in catalog"],
          ["100%", "Data-grounded answers"],
        ].map(([n, label]) => (
          <div key={label} className="text-center">
            <div className="text-3xl font-bold text-brand-600 dark:text-brand-300">{n}</div>
            <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
