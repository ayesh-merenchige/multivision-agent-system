"use client";

import { useEffect, useState } from "react";
import { Plus, Save, Trash2 } from "lucide-react";
import { getPricing, updatePricing, type Pricing } from "@/lib/api";
import { useToast } from "./Toast";

export default function PricingTab() {
  const toast = useToast();
  const [pricing, setPricing] = useState<Pricing>({ tiers: [], tax_pct: 0 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getPricing()
      .then(setPricing)
      .catch(() => toast("Failed to load pricing", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  function updateTier(index: number, field: "name" | "min_qty" | "discount_pct", value: string) {
    setPricing((p) => {
      const tiers = p.tiers.map((t, i) =>
        i === index
          ? { ...t, [field]: field === "name" ? value : Number(value) }
          : t
      );
      return { ...p, tiers };
    });
  }

  function addTier() {
    setPricing((p) => ({
      ...p,
      tiers: [...p.tiers, { name: `tier-${p.tiers.length + 1}`, min_qty: 1, discount_pct: 0 }],
    }));
  }

  function removeTier(index: number) {
    setPricing((p) => ({ ...p, tiers: p.tiers.filter((_, i) => i !== index) }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updatePricing(pricing);
      toast("Pricing saved");
    } catch (e: any) {
      toast(e.message || "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="py-8 text-center text-slate-400">Loading…</p>;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h3 className="mb-3 font-semibold">Volume discount tiers</h3>
        <div className="space-y-3">
          {pricing.tiers.map((tier, i) => (
            <div key={i} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <input
                className="input flex-1"
                value={tier.name}
                onChange={(e) => updateTier(i, "name", e.target.value)}
                placeholder="Tier name"
              />
              <input
                type="number"
                className="input w-24"
                value={tier.min_qty}
                onChange={(e) => updateTier(i, "min_qty", e.target.value)}
                placeholder="Min qty"
              />
              <input
                type="number"
                className="input w-24"
                value={tier.discount_pct}
                onChange={(e) => updateTier(i, "discount_pct", e.target.value)}
                placeholder="Discount %"
              />
              <span className="text-sm text-slate-400">% off</span>
              <button
                onClick={() => removeTier(i)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-900/30"
                aria-label="Remove tier"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
        <button
          onClick={addTier}
          className="mt-3 flex items-center gap-2 rounded-xl border border-dashed border-slate-300 px-4 py-2 text-sm text-slate-600 hover:border-brand-400 hover:text-brand-600 dark:border-slate-600 dark:text-slate-300"
        >
          <Plus size={15} /> Add tier
        </button>
      </div>

      <div>
        <h3 className="mb-3 font-semibold">Tax</h3>
        <div className="flex items-center gap-3">
          <input
            type="number"
            className="input w-32"
            value={pricing.tax_pct}
            onChange={(e) => setPricing((p) => ({ ...p, tax_pct: Number(e.target.value) }))}
          />
          <span className="text-sm text-slate-500">% applied at checkout</span>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
      >
        <Save size={16} /> {saving ? "Saving…" : "Save pricing"}
      </button>
    </div>
  );
}
