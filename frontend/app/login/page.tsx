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
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-lg bg-cyan/20 flex items-center justify-center">
            <Shield size={24} className="text-cyan" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AgentFinance</h1>
            <p className="text-xs text-text-muted">Control System</p>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">
            {isRegister ? "Create Account" : "Sign In"}
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
                  className="w-full bg-elevated border border-border rounded px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-cyan focus:ring-1 focus:ring-cyan/50"
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
                className="w-full bg-elevated border border-border rounded px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-cyan focus:ring-1 focus:ring-cyan/50"
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
                className="w-full bg-elevated border border-border rounded px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-cyan focus:ring-1 focus:ring-cyan/50"
                required
              />
            </div>
            {error && (
              <p className="text-sm text-red">{error}</p>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-cyan text-primary-foreground rounded py-2 text-sm font-medium hover:bg-cyan/90 disabled:opacity-50 transition-colors"
            >
              {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign In"}
            </button>
          </form>
        </div>

        <p className="text-sm text-text-muted mt-4 text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-cyan hover:underline"
          >
            {isRegister ? "Already have an account? Sign in" : "No account? Create one"}
          </button>
        </p>
      </div>
    </div>
  );
}
