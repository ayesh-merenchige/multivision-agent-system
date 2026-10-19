// Centralized, typed API client for the Multivisions backend.
// All fetch calls go through here so response shapes stay in one place.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types (mirror the backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface Company {
  name: string;
  tagline: string;
  description: string;
  email: string;
  phone: string;
  address: string;
  website: string;
  working_hours: string;
  socials: { linkedin: string; twitter: string; facebook: string };
}

export interface Product {
  id: string;
  name: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  stock: number;
  image_url: string;
  tags: string[];
  active: boolean;
}

export interface PricingTier {
  name: string;
  min_qty: number;
  discount_pct: number;
}

export interface Pricing {
  tiers: PricingTier[];
  tax_pct: number;
}

export interface OrderItem {
  id: number;
  order_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  id: string;
  customer_name: string;
  contact: string;
  address: string;
  notes: string | null;
  status: "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";
  total_amount: number;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface TraceEntry {
  agent: string;
  action: string;
  status: string;
  latency_ms: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  agent: string | null;
  created_at: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  intent: string;
  order_id: string | null;
  trace: TraceEntry[];
}

export interface NewSessionResponse {
  session_id: string;
  title: string;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  last_activity: string;
  message_count: number;
}

export interface OverviewStats {
  total_orders: number;
  revenue: number;
  active_sessions: number;
  agent_calls: number;
}

export interface AgentStat {
  agent: string;
  calls: number;
  avg_latency_ms: number;
  success_rate: number;
  last_called: string | null;
}

export interface TimelinePoint {
  date: string;
  orders: number;
  chats: number;
}

export interface ActivityEntry {
  id: number;
  session_id: string;
  agent: string;
  action: string;
  status: string;
  latency_ms: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export function newSession(): Promise<NewSessionResponse> {
  return request("/api/chat/new-session", { method: "POST" });
}

export function sendChat(sessionId: string, message: string): Promise<ChatResponse> {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}

export function getHistory(sessionId: string): Promise<{ session_id: string; messages: ChatMessage[] }> {
  return request(`/api/chat/history/${sessionId}`);
}

export function listSessions(): Promise<SessionSummary[]> {
  return request("/api/chat/sessions");
}

// ---------------------------------------------------------------------------
// Company / Products / Pricing
// ---------------------------------------------------------------------------

export function getCompany(): Promise<Company> {
  return request("/api/company");
}

export function updateCompany(company: Partial<Company>): Promise<Company> {
  return request("/api/company", { method: "PUT", body: JSON.stringify(company) });
}

export function listProducts(category?: string): Promise<Product[]> {
  const q = category ? `?category=${encodeURIComponent(category)}` : "";
  return request(`/api/products${q}`);
}

export function createProduct(product: Omit<Product, "id"> & { id: string }): Promise<Product> {
  return request("/api/products", { method: "POST", body: JSON.stringify(product) });
}

export function updateProduct(id: string, product: Partial<Product>): Promise<Product> {
  return request(`/api/products/${id}`, { method: "PUT", body: JSON.stringify(product) });
}

export function deleteProduct(id: string): Promise<void> {
  return request(`/api/products/${id}`, { method: "DELETE" });
}

export function getPricing(): Promise<Pricing> {
  return request("/api/pricing");
}

export function updatePricing(pricing: Partial<Pricing>): Promise<Pricing> {
  return request("/api/pricing", { method: "PUT", body: JSON.stringify(pricing) });
}

// ---------------------------------------------------------------------------
// Orders
// ---------------------------------------------------------------------------

export function listOrders(status?: string): Promise<Order[]> {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/orders${q}`);
}

export function getOrder(id: string): Promise<Order> {
  return request(`/api/orders/${id}`);
}

export function updateOrderStatus(id: string, status: string): Promise<Order> {
  return request(`/api/orders/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export function getOverview(): Promise<OverviewStats> {
  return request("/api/stats/overview");
}

export function getAgentStats(): Promise<AgentStat[]> {
  return request("/api/stats/agents");
}

export function getTimeline(days = 7): Promise<TimelinePoint[]> {
  return request(`/api/stats/timeline?days=${days}`);
}

export function getRecentActivity(limit = 20): Promise<ActivityEntry[]> {
  return request(`/api/stats/recent-activity?limit=${limit}`);
}

export function getOrdersByStatus(): Promise<{ status: string; count: number }[]> {
  return request("/api/stats/orders-by-status");
}

export { API_URL };
