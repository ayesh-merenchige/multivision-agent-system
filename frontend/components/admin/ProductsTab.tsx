"use client";

import { useEffect, useMemo, useState } from "react";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import {
  createProduct,
  deleteProduct,
  listProducts,
  updateProduct,
  type Product,
} from "@/lib/api";
import { useToast } from "./Toast";
import Modal from "./Modal";

const EMPTY_FORM = {
  id: "",
  name: "",
  category: "General",
  description: "",
  price: 0,
  currency: "USD",
  stock: 0,
  image_url: "",
  tags: "",
  active: true,
};

export default function ProductsTab() {
  const toast = useToast();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Product | null>(null);
  const [sortKey, setSortKey] = useState<"name" | "price" | "stock">("name");
  const [sortAsc, setSortAsc] = useState(true);

  async function refresh() {
    try {
      setProducts(await listProducts());
    } catch {
      toast("Failed to load products", "error");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const list = products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q)
    );
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortAsc ? cmp : -cmp;
    });
    return list;
  }, [products, search, sortKey, sortAsc]);

  function toggleSort(key: "name" | "price" | "stock") {
    if (sortKey === key) setSortAsc((v) => !v);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  function openAdd() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  }
  function openEdit(p: Product) {
    setEditing(p);
    setForm({
      id: p.id,
      name: p.name,
      category: p.category,
      description: p.description,
      price: p.price,
      currency: p.currency,
      stock: p.stock,
      image_url: p.image_url,
      tags: p.tags.join(", "),
      active: p.active,
    });
    setModalOpen(true);
  }

  async function handleSave() {
    setSaving(true);
    const payload = {
      id: form.id,
      name: form.name,
      category: form.category,
      description: form.description,
      price: Number(form.price),
      currency: form.currency,
      stock: Number(form.stock),
      image_url: form.image_url,
      tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      active: form.active,
    };
    try {
      if (editing) {
        await updateProduct(editing.id, payload);
        toast("Product updated");
      } else {
        await createProduct(payload);
        toast("Product created");
      }
      setModalOpen(false);
      await refresh();
    } catch (e: any) {
      toast(e.message || "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmDelete) return;
    try {
      await deleteProduct(confirmDelete.id);
      toast("Product deleted");
      setConfirmDelete(null);
      await refresh();
    } catch (e: any) {
      toast(e.message || "Delete failed", "error");
    }
  }

  async function toggleActive(p: Product) {
    try {
      await updateProduct(p.id, { active: !p.active });
      await refresh();
    } catch {
      toast("Update failed", "error");
    }
  }

  if (loading) return <p className="py-8 text-center text-slate-400">Loading…</p>;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="Search products…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          onClick={openAdd}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
        >
          <Plus size={16} /> Add product
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-400 dark:border-slate-800 dark:bg-slate-800/50">
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="cursor-pointer select-none px-4 py-3 font-medium" onClick={() => toggleSort("name")}>
                Name {sortKey === "name" ? (sortAsc ? "↑" : "↓") : ""}
              </th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="cursor-pointer select-none px-4 py-3 font-medium" onClick={() => toggleSort("price")}>
                Price {sortKey === "price" ? (sortAsc ? "↑" : "↓") : ""}
              </th>
              <th className="cursor-pointer select-none px-4 py-3 font-medium" onClick={() => toggleSort("stock")}>
                Stock {sortKey === "stock" ? (sortAsc ? "↑" : "↓") : ""}
              </th>
              <th className="px-4 py-3 font-medium">Active</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400">No products found.</td>
              </tr>
            )}
            {filtered.map((p) => (
              <tr key={p.id} className="border-b border-slate-100 last:border-0 dark:border-slate-800">
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{p.id}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {p.image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={p.image_url} alt="" className="h-8 w-8 rounded-lg object-cover" />
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-[10px] font-bold text-slate-400 dark:bg-slate-700">
                        {p.name.slice(0, 1)}
                      </div>
                    )}
                    <span className="font-medium">{p.name}</span>
                  </div>
                  {p.tags.length > 0 && (
                    <div className="mt-0.5 flex flex-wrap gap-1">
                      {p.tags.map((t) => (
                        <span key={t} className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500 dark:bg-slate-700 dark:text-slate-300">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{p.category}</td>
                <td className="px-4 py-3 font-medium">${p.price.toFixed(2)}</td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{p.stock}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleActive(p)}
                    className={`relative h-5 w-9 rounded-full transition ${p.active ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600"}`}
                    aria-label="Toggle active"
                  >
                    <span
                      className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all"
                      style={{ left: p.active ? "18px" : "2px" }}
                    />
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1">
                    <button onClick={() => openEdit(p)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-brand-600 dark:hover:bg-slate-700">
                      <Pencil size={15} />
                    </button>
                    <button onClick={() => setConfirmDelete(p)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-rose-600 dark:hover:bg-slate-700">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add/Edit modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Edit product" : "Add product"}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">ID</span>
              <input className="input" value={form.id} disabled={!!editing} onChange={(e) => setForm({ ...form, id: e.target.value })} placeholder="P011" />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Name</span>
              <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
          </div>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">Category</span>
            <input className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">Description</span>
            <textarea className="input min-h-20" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </label>
          <div className="grid grid-cols-3 gap-4">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Price</span>
              <input type="number" className="input" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Stock</span>
              <input type="number" className="input" value={form.stock} onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })} />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Currency</span>
              <input className="input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
            </label>
          </div>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">Tags (comma-separated)</span>
            <input className="input" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="iot, hub" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} className="h-4 w-4 rounded" />
            Active
          </label>
          <button
            onClick={handleSave}
            disabled={saving || !form.id || !form.name}
            className="w-full rounded-xl bg-gradient-to-r from-brand-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Saving…" : editing ? "Update product" : "Create product"}
          </button>
        </div>
      </Modal>

      {/* Delete confirm */}
      <Modal open={!!confirmDelete} onClose={() => setConfirmDelete(null)} title="Delete product">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Are you sure you want to delete <strong>{confirmDelete?.name}</strong>? This cannot be undone.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={() => setConfirmDelete(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-sm dark:border-slate-700">
            Cancel
          </button>
          <button onClick={handleDelete} className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700">
            Delete
          </button>
        </div>
      </Modal>
    </div>
  );
}
