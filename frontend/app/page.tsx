"use client";

import Link from "next/link";
import { Shield, Bot, FileText, CheckCircle, Lock, Activity } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan/20 flex items-center justify-center">
            <Shield size={18} className="text-cyan" />
          </div>
          <span className="font-bold">AgentFinance</span>
        </div>
        <div className="flex gap-3">
          <Link href="/login"><Button variant="ghost">Sign In</Button></Link>
          <Link href="/login"><Button>Get Started</Button></Link>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Control Your Autonomous<br />Financial Agents
          </h1>
          <p className="text-lg text-text-muted max-w-2xl mx-auto mb-8">
            Mission-control dashboard for supervising AI agents that handle real money.
            Set limits, enforce policies, approve payouts, and audit every transaction.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/login"><Button size="lg">Start Free</Button></Link>
            <a href="https://github.com/nek1912/innovaHack" target="_blank" rel="noopener noreferrer">
              <Button size="lg" variant="ghost">View on GitHub</Button>
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-20">
          {[
            { icon: Bot, title: "Agent Management", desc: "Create agents with per-transaction and daily spending caps. Freeze instantly with one click." },
            { icon: Shield, title: "OPA Policy Engine", desc: "Every payout evaluated against rules. Allow, approve, or deny — before money moves." },
            { icon: Lock, title: "Kill Switch", desc: "Freeze any agent instantly. All requests blocked at auth and policy layers." },
            { icon: Activity, title: "Live Dashboard", desc: "Real-time stats, approval queue, spend tracking. Auto-refreshes every 30 seconds." },
            { icon: FileText, title: "Full Audit Trail", desc: "Every action logged with request ID, actor, and structured detail. Filterable and paginated." },
            { icon: CheckCircle, title: "Webhook Verified", desc: "RazorpayX webhooks with HMAC-SHA256 verification. Idempotent processing. Reconciliation built in." },
          ].map((f) => (
            <div key={f.title} className="bg-surface border border-border rounded-lg p-6">
              <div className="w-10 h-10 rounded-lg bg-cyan/10 flex items-center justify-center mb-3">
                <f.icon size={20} className="text-cyan" />
              </div>
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-text-muted">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold mb-8">How It Works</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {["Create Agent", "Set Caps", "Add Payee", "Request Payout", "Policy Check", "Approve/Deny", "Execute", "Audit"].map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-full bg-cyan/20 text-cyan text-sm font-bold flex items-center justify-center">{i + 1}</span>
                <span className="text-sm">{step}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="bg-surface border border-border rounded-lg p-8 text-center">
          <h2 className="text-xl font-bold mb-2">Ready to take control?</h2>
          <p className="text-text-muted mb-4">Set up your first agent in under 2 minutes.</p>
          <Link href="/login"><Button size="lg">Get Started</Button></Link>
        </div>
      </div>

      <footer className="border-t border-border py-6 text-center text-sm text-text-muted">
        AgentFinance Control System
      </footer>
    </div>
  );
}
