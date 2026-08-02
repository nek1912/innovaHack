"use client";

import Link from "next/link";
import { Shield, Bot, FileText, CheckCircle, Lock, Activity, CreditCard, Brain, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 h-16">
        <span className="text-base font-medium text-text-primary">Autonomous Agent Credit Platform</span>
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
          Credit-for-Autonomous-Agents
        </p>
        <h1 className="text-5xl md:text-6xl font-normal text-text-primary leading-tight mb-6 max-w-3xl">
          Let AI agents spend <span className="text-info">company credit</span> safely
        </h1>
        <p className="text-lg text-text-muted mb-8 max-w-xl">
          Policy-enforced financial operating system where autonomous AI agents request funds,
          but all credit, limits, and approvals are controlled by the platform — not the AI.
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

      {/* Architecture Diagram */}
      <div className="border-t border-border-cool">
        <div className="max-w-screen-lg mx-auto px-8 py-16">
          <h2 className="text-2xl font-normal text-text-primary mb-10">How it works</h2>
          <div className="bg-surface-warm border border-border-warm rounded-[10px] p-8 font-mono text-sm">
            <div className="space-y-3 text-text-secondary">
              <div className="flex items-center gap-3">
                <span className="text-info">Owner</span>
                <span className="text-text-muted">→</span>
                <span>Creates Agent</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-info">Owner</span>
                <span className="text-text-muted">→</span>
                <span>Issues Credit (underwriting)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-success">Agent</span>
                <span className="text-text-muted">→</span>
                <span>Receives task (Groq LLM)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-success">Agent</span>
                <span className="text-text-muted">→</span>
                <span>Reasons → needs ₹1200</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-success">Agent</span>
                <span className="text-text-muted">→</span>
                <span>Calls request_payout()</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-warning">Platform</span>
                <span className="text-text-muted">→</span>
                <span>OPA evaluates (credit + caps)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-warning">Platform</span>
                <span className="text-text-muted">→</span>
                <span>Reserves credit</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-info">RazorpayX</span>
                <span className="text-text-muted">→</span>
                <span>Executes payout (Test Mode)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-info">Platform</span>
                <span className="text-text-muted">→</span>
                <span>Commits credit + audit</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-screen-lg mx-auto px-8 pb-20">
        <h2 className="text-2xl font-normal text-text-primary mb-10">Platform capabilities</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { icon: CreditCard, title: "Credit Engine", desc: "Issue credit after underwriting. Append-only ledger. Reserve before payout. Commit on success." },
            { icon: Brain, title: "Autonomous Agent", desc: "Groq LLM reasons about tasks. Requests funds. Cannot approve or modify policies." },
            { icon: Shield, title: "OPA Policy Engine", desc: "7 deny reasons. Credit checks. Cap enforcement. Approval thresholds. All audited." },
            { icon: TrendingUp, title: "Risk Scoring", desc: "Track late repayments, defaults, violations. Freeze on default. Recovery via repayment." },
            { icon: Lock, title: "Kill Switch", desc: "Freeze agent or credit instantly. All requests blocked at auth and policy layers." },
            { icon: Activity, title: "Full Audit Trail", desc: "Every credit event, payout, repayment, and agent action logged with request ID." },
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

      {/* Demo Scenarios */}
      <div className="border-t border-border-cool">
        <div className="max-w-screen-lg mx-auto px-8 py-16">
          <h2 className="text-2xl font-normal text-text-primary mb-10">Demo scenarios</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { task: "Buy GPU Compute", amount: "₹1,200", result: "Approved", desc: "Normal approval flow" },
              { task: "Purchase Dataset", amount: "₹3,500", result: "Approval Required", desc: "Above threshold" },
              { task: "Purchase Hardware", amount: "₹5,000", result: "Rejected", desc: "Unknown vendor" },
              { task: "API Subscription", amount: "₹600", result: "Approved", desc: "Under all limits" },
              { task: "Emergency Compute", amount: "₹15,000", result: "Credit Exhausted", desc: "Exceeds available" },
            ].map((s) => (
              <div key={s.task} className="flex items-center justify-between p-4 border border-border-warm rounded-[10px]">
                <div>
                  <p className="text-sm font-medium text-text-primary">{s.task}</p>
                  <p className="text-xs text-text-muted">{s.desc}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono text-text-primary">{s.amount}</p>
                  <p className={`text-xs font-medium ${
                    s.result === "Approved" ? "text-success" :
                    s.result === "Rejected" ? "text-danger" :
                    s.result === "Credit Exhausted" ? "text-danger" :
                    "text-warning"
                  }`}>{s.result}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-surface-warm border-t border-border-cool">
        <div className="max-w-screen-lg mx-auto px-8 py-16 text-center">
          <h2 className="text-2xl font-normal text-text-primary mb-2">Ready to control AI spending?</h2>
          <p className="text-text-muted mb-6">Issue credit, enforce policies, audit every transaction.</p>
          <Link href="/login">
            <Button size="lg">Get started</Button>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border-cool py-6 text-center text-sm text-text-muted">
        Autonomous Agent Credit Platform
      </footer>
    </div>
  );
}
