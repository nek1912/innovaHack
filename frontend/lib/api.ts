const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---- Typed response schemas matching backend ----

export interface Agent {
  id: string;
  name: string;
  status: string;
  per_tx_cap_paise: number;
  daily_cap_paise: number;
  approval_threshold_paise: number;
  api_key?: string;
}

export interface Payee {
  id: string;
  label: string;
  vpa: string | null;
  bank_account_number: string | null;
  bank_ifsc: string | null;
  active: boolean;
}

export interface PayoutDetail {
  id: string;
  agent_id: string;
  agent_name: string;
  payee_id: string;
  payee_label: string;
  amount_paise: number;
  mode: string;
  purpose: string | null;
  policy_decision: string;
  policy_reason: string | null;
  razorpay_payout_id: string | null;
  razorpay_status: string | null;
  created_at: string;
}

export interface AuditEntry {
  id: number;
  request_id: string;
  agent_id: string | null;
  owner_id: string | null;
  event_type: string;
  detail: Record<string, unknown> | null;
  created_at: string;
}

export interface DashboardStats {
  total_agents: number;
  active_agents: number;
  frozen_agents: number;
  total_payees: number;
  today_spend_paise: number;
  today_limit_paise: number;
  pending_approvals: number;
  failed_payouts: number;
  policy_violations: number;
  payment_success_rate: number | null;
  stale_payouts: number;
  local_error_payouts: number;
  last_reconciled_at: string | null;
  provider_mode: string | null;
  provider_configured: boolean;
}

export interface PayoutResponse {
  id: string;
  status: string;
  policy_decision: string;
  policy_reason: string | null;
}

export interface CreditAccountDetail {
  id: string;
  agent_id: string;
  credit_limit: number;
  available_credit: number;
  used_credit: number;
  reserved_credit: number;
  status: string;
}

export interface CreditTransaction {
  id: string;
  type: string;
  amount: number;
  balance_after: number;
  reason: string;
  created_at: string;
}

export interface CreditDashboardData {
  total_accounts: number;
  active_accounts: number;
  frozen_accounts: number;
  total_credit_limit: number;
  total_available: number;
  total_used: number;
  total_reserved: number;
}

export interface Repayment {
  id: string;
  due_date: string;
  amount: number;
  status: string;
  paid_amount: number;
  repayment_method: string;
}

export interface CreditRiskData {
  overall_risk: string;
  overall_score: number;
  total_violations: number;
  total_failures: number;
  total_defaults: number;
  total_frozen: number;
  agents: Array<{
    agent_id: string;
    agent_name: string;
    risk_level: string;
    risk_score: number;
    violations: number;
    failures: number;
    defaults: number;
    is_frozen: boolean;
  }>;
}

export interface OwnerToken {
  access_token: string;
  token_type: string;
}

// ---- API client ----

async function request<T>(path: string, options: RequestInit = {}, retries = 2): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_URL}${path}`, { ...options, headers });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg = body.message || body.detail || `HTTP ${res.status}`;
        throw new Error(msg);
      }
      return res.json();
    } catch (err) {
      if (attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, 300 * 2 ** attempt));
    }
  }
  throw new Error("unreachable");
}

export const api = {
  // Auth
  register: (name: string, email: string, password: string) =>
    request<OwnerToken>("/owner/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    request<OwnerToken>("/owner/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  // Agents
  listAgents: () => request<{ agents: Agent[] }>("/owner/agents"),

  getAgent: (id: string) => request<Agent>(`/owner/agents/${id}`),

  createAgent: (data: { name: string; per_tx_cap_paise: number; daily_cap_paise: number; approval_threshold_paise: number }) =>
    request<Agent>("/owner/agents", { method: "POST", body: JSON.stringify(data) }),

  freezeAgent: (id: string) =>
    request<{ status: string; agent_id: string }>(`/owner/agents/${id}/freeze`, { method: "POST" }),

  unfreezeAgent: (id: string) =>
    request<{ status: string; agent_id: string }>(`/owner/agents/${id}/unfreeze`, { method: "POST" }),

  // Payees
  listAgentPayees: (agentId: string) =>
    request<{ payees: Payee[] }>(`/owner/agents/${agentId}/payees`),

  createPayee: (agentId: string, data: { label: string; vpa?: string; bank_account_number?: string; bank_ifsc?: string }) =>
    request<Payee>(`/owner/agents/${agentId}/payees`, { method: "POST", body: JSON.stringify(data) }),

  setPayeeActive: (agentId: string, payeeId: string, active: boolean) =>
    request<Payee>(`/owner/agents/${agentId}/payees/${payeeId}`, { method: "PATCH", body: JSON.stringify({ active }) }),

  // Payouts
  listPayouts: (params: { status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) qs.set(k, String(v)); });
    return request<{ payouts: PayoutDetail[]; total: number }>(`/owner/payouts?${qs}`);
  },

  listAgentPayouts: (agentId: string, params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) qs.set(k, String(v)); });
    return request<{ payouts: PayoutDetail[]; total: number }>(`/owner/agents/${agentId}/payouts?${qs}`);
  },

  approvePayout: (id: string) =>
    request<{ status: string; payout_id: string }>(`/owner/payouts/${id}/approve`, { method: "POST" }),

  rejectPayout: (id: string) =>
    request<{ status: string; payout_id: string }>(`/owner/payouts/${id}/reject`, { method: "POST" }),

  requestPayout: (agentId: string, data: { payee_id: string; amount_paise: number; mode: string; purpose?: string }) =>
    request<PayoutResponse>(`/owner/agents/${agentId}/payouts`, { method: "POST", body: JSON.stringify(data) }),

  // Audit
  getAuditLog: (params: { agent_id?: string; event_type?: string; from?: string; to?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, String(v)); });
    return request<{ entries: AuditEntry[]; total: number }>(`/audit?${qs}`);
  },

  // Dashboard
  getStats: () => request<DashboardStats>("/owner/stats"),

  // Credit
  getCreditDashboard: () =>
    request<CreditDashboardData>("/owner/credit/dashboard"),

  getCreditRisk: () =>
    request<CreditRiskData>("/owner/credit/risk"),

  getCreditAccount: (agentId: string) =>
    request<CreditAccountDetail>(`/credit/account/${agentId}`),

  getCreditHistory: (agentId: string) =>
    request<{ transactions: CreditTransaction[]; total: number }>(`/credit/history/${agentId}`),

  freezeCredit: (agentId: string) =>
    request<{ status: string }>(`/owner/credit/freeze/${agentId}`, { method: "POST" }),

  unfreezeCredit: (agentId: string) =>
    request<{ status: string }>(`/owner/credit/unfreeze/${agentId}`, { method: "POST" }),

  // Repayments
  getRepayments: (agentId: string) =>
    request<{ repayments: Repayment[]; total: number }>(`/credit/repayments/${agentId}`),

  repayCredit: (repaymentId: string) =>
    request<{ id: string; status: string; paid_amount: number }>("/credit/repay", {
      method: "POST",
      body: JSON.stringify({ repayment_id: repaymentId }),
    }),
};
