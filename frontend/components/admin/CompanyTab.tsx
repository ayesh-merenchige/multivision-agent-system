"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { getCompany, updateCompany, type Company } from "@/lib/api";
import { useToast } from "./Toast";

const EMPTY: Company = {
  name: "",
  tagline: "",
  description: "",
  email: "",
  phone: "",
  address: "",
  website: "",
  working_hours: "",
  socials: { linkedin: "", twitter: "", facebook: "" },
};

export default function CompanyTab() {
  const toast = useToast();
  const [form, setForm] = useState<Company>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getCompany()
      .then(setForm)
      .catch(() => toast("Failed to load company", "error"))
      .finally(() => setLoading(false));
  }, [toast]);

  function set(field: keyof Company, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }
  function setSocial(field: keyof Company["socials"], value: string) {
    setForm((f) => ({ ...f, socials: { ...f.socials, [field]: value } }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await updateCompany(form);
      toast("Company details saved");
    } catch (e: any) {
      toast(e.message || "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="py-8 text-center text-slate-400">Loading…</p>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <Field label="Company name">
          <input className="input" value={form.name} onChange={(e) => set("name", e.target.value)} />
        </Field>
        <Field label="Tagline">
          <input className="input" value={form.tagline} onChange={(e) => set("tagline", e.target.value)} />
        </Field>
        <Field label="Description">
          <textarea className="input min-h-24" value={form.description} onChange={(e) => set("description", e.target.value)} />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Email">
            <input className="input" value={form.email} onChange={(e) => set("email", e.target.value)} />
          </Field>
          <Field label="Phone">
            <input className="input" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </Field>
        </div>
        <Field label="Address">
          <input className="input" value={form.address} onChange={(e) => set("address", e.target.value)} />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Website">
            <input className="input" value={form.website} onChange={(e) => set("website", e.target.value)} />
          </Field>
          <Field label="Working hours">
            <input className="input" value={form.working_hours} onChange={(e) => set("working_hours", e.target.value)} />
          </Field>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Field label="LinkedIn">
            <input className="input" value={form.socials.linkedin} onChange={(e) => setSocial("linkedin", e.target.value)} />
          </Field>
          <Field label="Twitter">
            <input className="input" value={form.socials.twitter} onChange={(e) => setSocial("twitter", e.target.value)} />
          </Field>
          <Field label="Facebook">
            <input className="input" value={form.socials.facebook} onChange={(e) => setSocial("facebook", e.target.value)} />
          </Field>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
        >
          <Save size={16} /> {saving ? "Saving…" : "Save changes"}
        </button>
      </div>

      {/* Live preview */}
      <div className="h-fit rounded-2xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-700 dark:bg-slate-800/50">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Live preview</h3>
        <h2 className="mt-3 text-2xl font-bold">{form.name || "Company name"}</h2>
        {form.tagline && <p className="mt-1 text-brand-600 dark:text-brand-300">{form.tagline}</p>}
        {form.description && <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{form.description}</p>}
        <div className="mt-4 space-y-1 text-sm text-slate-500 dark:text-slate-400">
          {form.email && <p>✉ {form.email}</p>}
          {form.phone && <p>☎ {form.phone}</p>}
          {form.address && <p>⚲ {form.address}</p>}
          {form.working_hours && <p>🕒 {form.working_hours}</p>}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
      {children}
    </label>
  );
}
