"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Shield } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = isRegister
        ? () => api.register(name, email, password)
        : () => api.login(email, password);
      const { access_token } = await fn();
      localStorage.setItem("token", access_token);
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas">
      <div className="w-full max-w-sm px-4">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-full bg-surface-warm flex items-center justify-center">
            <Shield size={20} className="text-text-muted" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="text-base font-medium text-text-primary">AgentFinance</h1>
            <p className="text-xs text-text-muted">Control System</p>
          </div>
        </div>

        <div className="border border-border-warm rounded-[10px] p-6">
          <h2 className="text-lg font-medium text-text-primary mb-4">
            {isRegister ? "Create account" : "Sign in"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Name</label>
                <input
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-ink transition-colors"
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Email</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-ink transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-canvas border border-border-warm rounded-[10px] h-10 px-4 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-ink transition-colors"
                required
              />
            </div>
            {error && (
              <p className="text-sm text-danger">{error}</p>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-lime text-ink border-none rounded-[6px] h-10 text-sm font-medium hover:bg-lime-hover disabled:opacity-50 transition-colors cursor-pointer"
            >
              {loading ? "Please wait..." : isRegister ? "Create account" : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-sm text-text-muted mt-4 text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-text-primary hover:underline cursor-pointer"
          >
            {isRegister ? "Already have an account? Sign in" : "No account? Create one"}
          </button>
        </p>
      </div>
    </div>
  );
}
