"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  Bot,
  DollarSign,
  MessageSquare,
  RefreshCw,
  ShoppingCart,
} from "lucide-react";
import {
  getAgentStats,
  getOrdersByStatus,
  getOverview,
  getRecentActivity,
  getTimeline,
  listOrders,
  type ActivityEntry,
  type AgentStat,
  type Order,
  type OverviewStats,
  type TimelinePoint,
} from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "#f59e0b",
  confirmed: "#3b82f6",
  shipped: "#8b5cf6",
  delivered: "#10b981",
  cancelled: "#f43f5e",
};

const AGENT_COLORS: Record<string, string> = {
  supervisor: "#64748b",
  chat: "#8b5cf6",
  catalog: "#3b82f6",
  order: "#10b981",
};

function usePolling(callback: () => void, ms: number) {
  useEffect(() => {
    const id = setInterval(callback, ms);
    return () => clearInterval(id);
  }, [callback, ms]);
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [agents, setAgents] = useState<AgentStat[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [byStatus, setByStatus] = useState<{ status: string; count: number }[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  async function refresh() {
    try {
      const [ov, ag, tl, ac, od, bs] = await Promise.all([
        getOverview(),
        getAgentStats(),
        getTimeline(7),
        getRecentActivity(20),
        listOrders(),
        getOrdersByStatus(),
      ]);
      setOverview(ov);
      setAgents(ag);
      setTimeline(tl);
      setActivity(ac);
      setOrders(od.slice(0, 8));
      setByStatus(bs);
      setLastUpdated(new Date());
    } catch {
      /* ignore transient errors */
    }
  }

  usePolling(refresh, 5000);
  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const agentsRunning = activity.some(
    (a) => Date.now() - new Date(a.created_at).getTime() < 60_000
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Live agent & system monitoring · updated {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
            <span className={`h-2 w-2 rounded-full ${agentsRunning ? "bg-emerald-500 animate-pulse-dot" : "bg-slate-400"}`} />
            {agentsRunning ? "Agents running" : "Idle"}
          </span>
          <button
            onClick={refresh}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard icon={ShoppingCart} label="Total orders" value={overview?.total_orders ?? "—"} accent="from-brand-500 to-orange-600" />
        <KpiCard icon={DollarSign} label="Revenue" value={overview ? `$${overview.revenue.toLocaleString()}` : "—"} accent="from-emerald-500 to-teal-600" />
        <KpiCard icon={MessageSquare} label="Active sessions (24h)" value={overview?.active_sessions ?? "—"} accent="from-amber-500 to-orange-600" />
        <KpiCard icon={Bot} label="Agent calls (24h)" value={overview?.agent_calls ?? "—"} accent="from-sky-500 to-blue-600" />
      </div>

      {/* Charts row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 font-semibold">Orders & chats — last 7 days</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={(d: string) => d.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="orders" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="chats" fill="#a78bfa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 font-semibold">Orders by status</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={byStatus}
                  dataKey="count"
                  nameKey="status"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {byStatus.map((entry) => (
                    <Cell key={entry.status} fill={STATUS_COLORS[entry.status] ?? "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Agent activity + recent activity */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 font-semibold">Agent activity</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400 dark:border-slate-800">
                  <th className="pb-2 pr-3 font-medium">Agent</th>
                  <th className="pb-2 pr-3 font-medium">Calls</th>
                  <th className="pb-2 pr-3 font-medium">Avg latency</th>
                  <th className="pb-2 pr-3 font-medium">Success</th>
                  <th className="pb-2 font-medium">Last called</th>
                </tr>
              </thead>
              <tbody>
                {agents.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-400">
                      No agent activity yet — start a chat.
                    </td>
                  </tr>
                )}
                {agents.map((a) => (
                  <tr key={a.agent} className="border-b border-slate-50 last:border-0 dark:border-slate-800">
                    <td className="py-2.5 pr-3">
                      <span
                        className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
                        style={{ backgroundColor: AGENT_COLORS[a.agent] ?? "#64748b" }}
                      >
                        {a.agent}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 font-medium">{a.calls}</td>
                    <td className="py-2.5 pr-3 text-slate-500 dark:text-slate-400">{a.avg_latency_ms} ms</td>
                    <td className="py-2.5 pr-3">
                      <span className={a.success_rate >= 90 ? "text-emerald-600" : "text-amber-600"}>
                        {a.success_rate}%
                      </span>
                    </td>
                    <td className="py-2.5 text-slate-500 dark:text-slate-400">
                      {a.last_called ? new Date(a.last_called).toLocaleTimeString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 flex items-center gap-2 font-semibold">
            <Activity size={16} /> Recent activity
          </h2>
          <div className="max-h-80 space-y-2 overflow-y-auto">
            {activity.length === 0 && (
              <p className="py-6 text-center text-sm text-slate-400">No activity yet.</p>
            )}
            {activity.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-sm dark:border-slate-800"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11px] font-medium text-white"
                    style={{ backgroundColor: AGENT_COLORS[a.agent] ?? "#64748b" }}
                  >
                    {a.agent}
                  </span>
                  <span className="text-slate-600 dark:text-slate-300">{a.action}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className={a.status === "success" ? "text-emerald-600" : "text-rose-500"}>
                    {a.status}
                  </span>
                  <span>{a.latency_ms}ms</span>
                  <span>{new Date(a.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Orders table */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-4 font-semibold">Recent orders</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400 dark:border-slate-800">
                <th className="pb-2 pr-3 font-medium">Order</th>
                <th className="pb-2 pr-3 font-medium">Customer</th>
                <th className="pb-2 pr-3 font-medium">Items</th>
                <th className="pb-2 pr-3 font-medium">Total</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400">No orders yet.</td>
                </tr>
              )}
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-slate-50 last:border-0 dark:border-slate-800">
                  <td className="py-2.5 pr-3 font-medium text-brand-600 dark:text-brand-300">{o.id}</td>
                  <td className="py-2.5 pr-3">{o.customer_name}</td>
                  <td className="py-2.5 pr-3 text-slate-500 dark:text-slate-400">
                    {o.items.reduce((n, i) => n + i.quantity, 0)} item(s)
                  </td>
                  <td className="py-2.5 pr-3 font-medium">${o.total_amount.toFixed(2)}</td>
                  <td className="py-2.5">
                    <span
                      className="rounded-full px-2.5 py-0.5 text-xs font-medium capitalize"
                      style={{
                        backgroundColor: `${STATUS_COLORS[o.status]}22`,
                        color: STATUS_COLORS[o.status],
                      }}
                    >
                      {o.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: any;
  label: string;
  value: string | number;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br text-white ${accent}`}>
          <Icon size={18} />
        </span>
      </div>
      <div className="mt-3 text-3xl font-bold">{value}</div>
    </div>
  );
}
