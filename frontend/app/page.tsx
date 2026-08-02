"use client";

import Link from "next/link";
import { Shield, Bot, FileText, CheckCircle, Lock, Activity } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 h-16">
        <span className="text-base font-medium text-text-primary">TrustPay</span>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link href="/login">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-screen-lg mx-auto px-8 pt-20 pb-16">
        <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted mb-4">
          Agent Finance
        </p>
        <h1 className="text-5xl md:text-6xl font-normal text-text-primary leading-tight mb-6 max-w-3xl">
          Control your autonomous financial agents
        </h1>
        <p className="text-lg text-text-muted mb-8 max-w-xl">
          Mission-control dashboard for supervising AI agents that handle real money.
          Set limits, enforce policies, approve payouts, and audit every transaction.
        </p>
        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button size="lg">Get started for free</Button>
          </Link>
          <a href="https://github.com/nek1912/innovaHack" target="_blank" rel="noopener noreferrer">
            <Button variant="ghost" size="lg">View on GitHub</Button>
          </a>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-screen-lg mx-auto px-8 pb-20">
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { icon: Bot, title: "Agent Management", desc: "Create agents with per-transaction and daily spending caps. Freeze instantly." },
            { icon: Shield, title: "OPA Policy Engine", desc: "Every payout evaluated against rules. Allow, approve, or deny before money moves." },
            { icon: Lock, title: "Kill Switch", desc: "Freeze any agent instantly. All requests blocked at auth and policy layers." },
            { icon: Activity, title: "Live Dashboard", desc: "Real-time stats, approval queue, spend tracking. Auto-refreshes every 30 seconds." },
            { icon: FileText, title: "Full Audit Trail", desc: "Every action logged with request ID, actor, and structured detail." },
            { icon: CheckCircle, title: "Webhook Verified", desc: "RazorpayX webhooks with HMAC-SHA256 verification. Idempotent processing." },
          ].map((f) => (
            <div key={f.title} className="border border-border-warm rounded-[10px] p-6">
              <div className="w-10 h-10 rounded-full bg-surface-warm flex items-center justify-center mb-4">
                <f.icon size={18} className="text-text-muted" strokeWidth={1.5} />
              </div>
              <h3 className="text-sm font-medium text-text-primary mb-2">{f.title}</h3>
              <p className="text-sm text-text-muted leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div className="border-t border-border-cool">
        <div className="max-w-screen-lg mx-auto px-8 py-16">
          <h2 className="text-2xl font-normal text-text-primary mb-10">How it works</h2>
          <div className="flex flex-wrap gap-6">
            {["Create Agent", "Set Caps", "Add Payee", "Request Payout", "Policy Check", "Approve/Deny", "Execute", "Audit"].map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-full bg-surface-warm text-text-secondary text-xs font-medium flex items-center justify-center">
                  {i + 1}
                </span>
                <span className="text-sm text-text-primary">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-surface-warm border-t border-border-cool">
        <div className="max-w-screen-lg mx-auto px-8 py-16 text-center">
          <h2 className="text-2xl font-normal text-text-primary mb-2">Ready to take control?</h2>
          <p className="text-text-muted mb-6">Set up your first agent in under 2 minutes.</p>
          <Link href="/login">
            <Button size="lg">Get started</Button>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border-cool py-6 text-center text-sm text-text-muted">
        TrustPay Control System
      </footer>
    </div>
  );
}
