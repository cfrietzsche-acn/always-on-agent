# Always-On Ops Agent — Pitch

---

## The Problem

Engineering and legal teams face two recurring time sinks that hit at the worst possible moments.

**Incident triage at 3am.** An on-call engineer wakes up to five open production tickets with no assigned severity, no context, and no obvious connection between them. They spend 45 minutes manually cross-referencing issue bodies, deploy logs, and runbooks — trying to figure out which two tickets are actually the same problem, which deploy broke what, and whether rolling back is even an option. By the time they have a hypothesis, the customer has already escalated. And the answer was sitting in the data the whole time.

**Vendor contract compliance.** A contract renewal comes up or a risk review is scheduled. Someone manually reads three vendor agreements against a compliance checklist. It takes a lawyer two or more hours, human error is common, and the breach notification clause that says "in due course" — a direct GDPR Article 33 violation — gets missed. Until it doesn't.

Both problems share the same root cause: **they are pattern-matching across structured data, and humans are slow at it, especially under pressure.**

---

## How We Approached It

We started with a synthetic enterprise ops repository that mirrors what a real engineering org already has: open incident tickets, recent deploy logs, diagnostic runbooks, vendor contracts, and a compliance policy. No new schema. No database. No integration work.

We built a Claude-powered agent that reads this data autonomously, reasons across it, and writes a cited report. The agent is not given rules or lookup tables. It decides which files to read, in what order, and what the connections mean — the same way a skilled engineer would, except it takes 90 seconds instead of 45 minutes.

The architecture is a standard Anthropic tool-use loop: the agent calls file-reading tools, receives the data, reasons across it, calls more tools as needed, and writes its findings as a persistent report. The reasoning streams live to the terminal so you can follow along in real time.

---

## What the Demo Shows

Run one command:

```bash
python main.py demo
```

### Act 1 — Incident Triage

The terminal begins streaming the agent's reasoning word-by-word as it works. You watch it:

- Call `list_issues()` — five open PROD incidents appear, none with assigned severity
- Call `read_issue()` on each one — reading every body before forming any hypothesis
- Call `list_deploys()` — pulling the full deploy history and calculating timestamp deltas
- Call `search_runbook()` for the services involved — pulling the diagnostic playbooks
- Reason across all of it and call `write_report()` as its final act

**What the output shows:**

PROD-4487 and PROD-4521 are two separate ticket numbers — a customer complaint and an NPE alert — that the agent identifies as the same cascading failure. The payment-service deploy at 14:04 introduced a null-pointer exception. The tenant-config-service deploy at 07:12 the next morning activated the guest-checkout feature flag for the affected customer cohort. Twenty-one minutes later, the customer complaint opened. The agent traces this from timestamps alone, with no hardcoded rules, and recommends an immediate rollback of the config deploy and a null-check fix at `PaymentService.java:142` before re-enabling the feature.

A separate upload latency issue is traced to the signing-service reducing a URL TTL from 3600 seconds to 300 — a security change that caused pre-signed URLs to expire mid-upload. An auth issue is flagged for DB connection pool exhaustion with the exact config key to change. A feature request is correctly classified P3 with no deploy correlation and no action required.

**The finding a human would miss:** the two checkout incidents are the same problem disguised as two tickets. The agent finds it in 90 seconds. An on-call engineer, reading tickets sequentially at 3am, typically would not.

Press Enter to continue to Act 2.

### Act 2 — Compliance Audit

Same agent, new mode. You watch it:

- Call `read_compliance_policy()` first — reads every rule before opening any contract
- Call `read_contract()` on each vendor agreement — reads in full
- Evaluate every clause against every rule
- Write a report with verbatim quotes and risk levels

**What the output shows:**

An executive summary table: Sirius Storage has six violations, five of them Critical. Acme Data Platform has three. Globex is fully compliant. Then the per-vendor detail — each violation quoted verbatim from the contract, rated by risk, with a specific remediation.

The Sirius Storage breach notification clause reads: *"Sirius will notify the customer of confirmed security incidents in due course, taking into account the nature and circumstances of the incident."* No defined window. The agent flags this Critical and calls it what it is: a GDPR Article 33 violation. The compliance policy requires 72 hours. "In due course" is not a timeline.

The Sirius termination clause prohibits termination for convenience during the initial five-year term. The liability cap is three months of fees — the policy minimum is twelve. The audit rights clause requires 180 days' notice, against a policy maximum of 90. Every violation is quoted, not paraphrased.

**The finding a human would miss:** Sirius Storage has six violations across seven policy rules. In a manual review, it is common to catch the headline issues and miss the subprocessor and governing-law clauses. The agent evaluates every rule against every contract and leaves nothing unchecked.

### After the demo ends

Two report files sit in `agent/reports/`:

- `triage-YYYY-MM-DD.md` — ranked incident findings with root causes, contributing deploys, and specific fixes
- `compliance-audit-YYYY-MM-DD.md` — violation table with verbatim quotes, risk levels, and remediation steps

These are not chat responses. They are persistent artifacts an on-call engineer can act on immediately, a legal team can attach to a contract review, and a post-mortem can reference six months later.

---

## The Always-On Loop

The demo also runs as a continuous loop — the "always-on" proof:

**Terminal 1:**
```bash
python main.py watch
```
Monitors `issues/` for new ticket files. When one appears, it triages it automatically.

**Terminal 2:**
```bash
python main.py generate --loop
```
Drops a new synthetic incident every 60 seconds, each paired with a matching deploy that arrived 15-20 minutes before the ticket. Scenarios cycle through: payment NPE spreading to new tenants, auth service memory leak, Stripe webhook failures, job queue backup, CDN cache cascade.

The watch terminal detects each new file, runs a focused triage, finds the deploy correlation, matches the runbook, and writes a per-ticket report — automatically, continuously, without a human in the loop.

---

## How This Would Actually Help

**For engineering:** The agent becomes the first responder on every incident. Before a human picks up the page, the agent has already correlated the ticket to a deploy, matched it to a runbook, and produced a starting hypothesis with cited evidence. The on-call engineer starts with a confirmed direction instead of a blank page. Mean time to hypothesis drops from 45 minutes to under 2 minutes.

**For legal and compliance:** Every vendor contract is audited against every policy rule on a schedule, not on a deadline. Contract renewals, new vendor onboarding, and annual risk reviews become agent-triggered reports rather than manual exercises. Violations are caught before they become incidents, not after.

**For leadership:** The agent's output is auditable. Every finding traces back to a specific file, field, timestamp, or verbatim clause. There is no black box. When the agent says a contract violates GDPR Article 33, it shows you the exact sentence in the contract and the exact rule it violates.

---

## What We Would Build Next

### Already done — MVP

- Autonomous triage across incidents, deploys, and runbooks
- Autonomous compliance audit across vendor contracts and policy
- Streaming output — reasoning visible in real time
- Watch mode — auto-triage on new ticket arrival
- Ticket generator — continuous demo loop

### Next sprint — Production hardening (P1)

| Feature | Why it matters |
|---------|----------------|
| Prompt caching on policy + contracts | ~90% cost reduction on repeated audit runs — policy never changes between runs |
| Eval harness with fixture assertions | Prevents prompt regressions as the system evolves — known correlations are automatically verified |
| Retry and error handling | Production resilience — current loop has no retry on transient API errors |
| Per-run cost and latency logging | Needed before any production deployment — visibility into what each run costs |

### Next phase — Connect to real systems (P2)

| Feature | Why it matters |
|---------|----------------|
| Live incident feed via PagerDuty or Jira webhook | Moves from synthetic data to real production incidents — the agent becomes operational |
| Slack or Teams notification tool | Agent routes findings to the on-call channel instead of writing a file — closes the action loop |
| Multi-agent architecture | Triage agent and audit agent run in parallel, orchestrated by a router — faster results, cleaner separation |
| Human-in-the-loop approval for P0 actions | Agent proposes remediation, human approves before execution — safe automation at the sharp end |
| Persistent memory across runs | Agent remembers what it already investigated and doesn't re-triage closed incidents |

### Six-month vision

An always-on enterprise intelligence layer that monitors incident feeds, deploy pipelines, and contract repositories continuously. It surfaces risk before humans notice it. It generates and routes remediation tickets. It builds institutional memory that persists across team changes, on-call rotations, and contract cycles.

The path is linear: **the MVP proves the reasoning works. P1 proves it works at production scale. P2 proves it integrates with the stack you already have.**

---

*Always-On Ops Agent — BTS AI Hackathon, May 2026*
