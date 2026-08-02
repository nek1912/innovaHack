For your project, I would **not** use that prompt as-is.

The strongest counterargument is that it is an excellent prompt for marketing websites, portfolios, SaaS landing pages, or branding work, but your application is a **mission-critical financial control dashboard**. If Claude follows those instructions literally, it will likely optimize for uniqueness over clarity and may introduce visual decisions that reduce usability.

That criticism survives scrutiny.

The corrected version should preserve the parts about deliberate design while replacing "distinctive for its own sake" with **trust, observability, and operational clarity**.

---

# Design Philosophy for Agent Finance Control System

## Core Objective

Design a production-grade financial command center that enables humans to supervise autonomous AI agents handling real money.

The interface must communicate:

* Trust
* Control
* Transparency
* Accountability
* Immediate understanding

This is **not**:

* a fintech marketing website
* a crypto dashboard
* a startup landing page
* a trading platform
* a consumer banking app

It is an **AI Operations + Financial Control Center**.

Think:

> "Mission Control for Autonomous Financial Agents"

instead of

> "Modern SaaS Dashboard"

---

# Subject

Product

Agent Finance Control System

Audience

* Finance teams
* Business owners
* Compliance officers
* Developers deploying AI agents
* Enterprise administrators

Primary Job

Allow humans to safely delegate financial authority to AI while maintaining complete visibility and instant control.

Every design decision should reinforce that objective.

---

# Core Product Principles

The interface should make the owner feel:

"I know exactly what every AI agent is doing."

not

"This looks cool."

Every screen answers one question:

"What money can move?"

"What already moved?"

"What will move next?"

"What stopped?"

"Why?"

---

# Visual Personality

Keywords

Operational

Calm

Industrial

Precise

Transparent

Confident

Minimal

Systematic

No marketing gradients.

No glowing glassmorphism.

No giant illustrations.

No floating blobs.

No fake analytics.

---

# Inspiration

Instead of copying fintech SaaS...

Study:

Stripe Dashboard

GitHub Actions

Cloudflare Zero Trust

AWS IAM Console

Datadog

Grafana

Linear

Raycast

OpenAI Platform

Not because they look similar,

but because they communicate operational state extremely well.

---

# Information Hierarchy

Priority

1. Active Alerts

2. Pending Approvals

3. Frozen Agents

4. Active Transactions

5. Daily Exposure

6. Agent Status

7. Audit Events

Everything else is secondary.

---

# Signature Design Element

Avoid decorative hero graphics.

Instead,

The application's identity should come from

a real-time "Financial Permission Graph."

Example

```
Owner
   │
   │ approves
   ▼

Agent A
   │
   ├──────────────► Vendor A

   ├──────────────► API Provider

   └──── blocked ─► Unknown Payee
```

As actions occur,

connections animate.

Blocked requests become red.

Approved become green.

Pending pulse amber.

This becomes the visual identity.

Not gradients.

Not illustrations.

---

# Color System

Use semantic colors.

Never use colors only because they look modern.

```
Background
#0B1118

Surface
#121A24

Elevated
#18222E

Primary Text
#F5F7FA

Secondary Text
#9CA8B6

Border
#2A3948

Success
#22C55E

Warning
#F59E0B

Danger
#EF4444

Info
#3B82F6

Approval
#06B6D4
```

Everything derives from system state.

---

# Typography

Display

IBM Plex Sans

Body

Inter

Data

JetBrains Mono

Reason

IBM Plex was designed for technical systems.

JetBrains Mono makes IDs, transaction hashes, policy names and logs readable.

Avoid oversized typography.

Numbers matter more than slogans.

---

# Layout

Think command center.

```
----------------------------------------
Top Navigation
----------------------------------------

Sidebar

Dashboard

----------------------------------------

Risk Summary

Pending Approvals

Active Agents

Recent Transactions

Audit Timeline

Policy Violations

----------------------------------------
```

Spacing is consistent.

Everything aligns to an 8px grid.

---

# Motion

Animation exists only to communicate change.

Examples

Agent freezes

↓

Card transitions to disabled

↓

Node in permission graph disconnects

↓

Transaction queue stops

↓

Toast appears

No decorative animations.

---

# Components

Every component represents an operational concept.

Examples

Agent Card

Shows

Status

Current Spend

Daily Limit

Approval Threshold

Last Activity

Freeze Button

Nothing decorative.

---

Approval Queue

Shows

Amount

Payee

Risk Score

Reason

Approve

Reject

---

Transaction Timeline

Chronological

Color-coded

Clickable

Shows

Request

Policy Check

Approval

Provider

Settlement

Complete story.

---

Audit Log

Looks like terminal output.

Every row

Timestamp

Actor

Action

Result

Metadata

Searchable.

---

Policy Inspector

Unique feature.

When a payout is denied,

show

```
Policy Evaluation

✓ Agent Active

✓ Payee Active

✓ Daily Limit OK

✗ Per Transaction Limit

Decision

Denied
```

Instead of

"Request failed."

This immediately explains why.

---

# Copy Style

Avoid marketing.

Instead of

"Empowering AI Finance"

write

"2 payouts awaiting approval"

Instead of

"Advanced Security"

write

"Agent frozen"

Everything is factual.

---

# Accessibility

Keyboard-first.

Every action reachable without a mouse.

High contrast.

Reduced motion respected.

Large clickable areas.

Screen-reader labels.

---

# What to Avoid

Do not build:

* Generic admin dashboard
* Crypto exchange UI
* TradingView clone
* Banking homepage
* Neon cyberpunk
* Glassmorphism
* Floating metric cards without purpose
* Hero sections inside the application
* Decorative charts

Every visualization must represent real system state.

---

# Master Instruction for Claude

```
You are the principal product designer and frontend architect for a production-grade Agent Finance Control System.

Do not generate generic SaaS dashboards.

Do not copy Stripe, Vercel, Linear, or any existing product.

Instead, study how operational software communicates trust, risk, and control.

Every UI component must represent a real financial concept.

Every color must represent system state.

Every animation must communicate state change.

Every chart must answer an operational question.

Prioritize observability over aesthetics.

Design for owners supervising autonomous AI agents handling real money.

The interface should feel like an AI Financial Operations Center rather than a fintech startup.

Before implementing any page:

1. Define the user's task.
2. Define the operational decisions they need to make.
3. Design the shortest path to those decisions.
4. Remove any component that does not improve supervision, safety, or transparency.

When uncertain, choose clarity over novelty.
```

I would use this in place of the original prompt because it is tailored to your domain. It aligns the design with the actual purpose of the product rather than encouraging visual distinctiveness that could conflict with a financial control interface.
