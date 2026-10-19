"use client";

import { useState } from "react";
import { Building2, DollarSign, Package } from "lucide-react";
import { ToastProvider } from "@/components/admin/Toast";
import CompanyTab from "@/components/admin/CompanyTab";
import ProductsTab from "@/components/admin/ProductsTab";
import PricingTab from "@/components/admin/PricingTab";

type Tab = "company" | "products" | "pricing";

const TABS: { id: Tab; label: string; icon: any }[] = [
  { id: "company", label: "Company", icon: Building2 },
  { id: "products", label: "Products", icon: Package },
  { id: "pricing", label: "Pricing", icon: DollarSign },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("company");

  return (
    <ToastProvider>
      <div className="animate-fade-in">
        <h1 className="text-2xl font-bold">Admin</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Manage company details, products, and pricing. Changes persist to the JSON data store.
        </p>

        <div className="mt-5 flex gap-1 rounded-2xl border border-slate-200 bg-white p-1 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
                tab === id
                  ? "bg-gradient-to-r from-brand-500 to-orange-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {tab === "company" && <CompanyTab />}
          {tab === "products" && <ProductsTab />}
          {tab === "pricing" && <PricingTab />}
        </div>
      </div>
    </ToastProvider>
  );
}
