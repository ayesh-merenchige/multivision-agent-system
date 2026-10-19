"use client";

import { CheckCircle2, Package } from "lucide-react";
import type { Order } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  confirmed: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  shipped: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  delivered: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  cancelled: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
};

export default function OrderCard({ order }: { order: Order }) {
  return (
    <div className="mt-2 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 size={18} />
          Order {order.id}
        </div>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[order.status]}`}>
          {order.status}
        </span>
      </div>
      <div className="mt-3 space-y-1.5">
        {order.items.map((item) => (
          <div key={item.id} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Package size={14} className="text-slate-400" />
              {item.product_name} <span className="text-slate-400">× {item.quantity}</span>
            </span>
            <span className="font-medium">${item.subtotal.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-700">
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {order.customer_name}
        </span>
        <span className="text-lg font-bold text-slate-800 dark:text-slate-100">
          ${order.total_amount.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
