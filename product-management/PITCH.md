# Always-On Ops Agent — 2-Minute Pitch

---

## The Problem

Every engineering organization has two recurring time sinks that happen at the worst possible moments:

**Incident triage at 3am.** An on-call engineer wakes up to five open production tickets. They spend 45 minutes manually cross-referencing issue bodies, deploy logs, and runbooks — trying to figure out which two tickets are actually the same problem, which deploy broke what, and whether rolling back is even an option. By the time they have a hypothesis, the customer has already escalated.

**Legal review of vendor contracts.** A contract renewal comes up or a risk review is scheduled. Someone manually reads three vendor agreements against a compliance policy checklist. It takes a lawyer 2+ hours, human error is common, and the "in due course" breach notification clause that violates GDPR Article 33 gets missed — until it doesn't.

Both problems share the same root cause: **they're pattern-matching across structured data, and humans are slow at it.**

---

## What We Built

An always-on enterprise ops agent that runs two autonomous modes against your existing repository data — no new infrastructure, no schema changes.

**Triage mode:** The agent reads every open incident, correlates them against your deploy history within a 48-hour window, cross-references your runbooks, and produces a cited, ranked report. It surfaces connections a human would miss — like two separate ticket numbers that are actually the same NPE triggered by a feature flag that went live 21 minutes before the customer complaint.

**Audit mode:** The agent reads your vendor contracts against your compliance policy and produces a violation report with verbatim contract quotes, risk levels, and remediation steps. It catches the clauses that say "in due course" where your policy requires 72 hours — the kind of thing that causes GDPR exposure.

**Both modes run in under 90 seconds.** On the same data that's already in your repo.

---

## Why It Matters

This isn't a demo of AI generating text. This is AI doing work that currently requires a senior engineer with 45 minutes of uninterrupted focus, or a contract lawyer with 2 hours and a checklist.

Three things make this different from a chatbot:

1. **It reads everything before it concludes.** Every issue body. Every deploy. Every runbook. It doesn't hallucinate — it cites the specific file, field, and timestamp behind every finding.

2. **It surfaces connections, not summaries.** The agent found that PROD-4487 and PROD-4521 — two separate ticket numbers — share the same root cause at `PaymentService.java:142`, triggered by a guest-checkout feature flag that went live for one customer cohort. A human reading tickets in order would likely triage them separately.

3. **It writes a report as its final act.** Not a chat response. A persistent markdown artifact that your on-call engineer can act on, your legal team can review, and your post-mortem can reference.

---

## The Demo in 90 Seconds

```
$ python main.py triage
  → list_issues()
  → read_issue(PROD-4487) ... read_issue(PROD-4521)
  → list_deploys()
  → search_runbook(payment-service-degraded)
  → write_report(triage-2026-05-27.md)
```

Open the report. PROD-4487 and PROD-4521 are linked — same root cause, two deploys, fix is a null check at one line of code. On-call engineer has a confirmed hypothesis in 90 seconds instead of 45 minutes.

```
$ python main.py audit
  → read_compliance_policy()
  → read_contract(sirius-storage)
  → write_report(compliance-audit-2026-05-27.md)
```

Open the report. Sirius Storage: 6 violations, 5 Critical. Breach notification says "in due course" — no defined window. That's a GDPR Article 33 timebomb. Flagged. Quoted verbatim. Remediation suggested.

---

## What Comes Next

### Next Sprint — Make it real-time (P1)

| Feature | What it unlocks |
|---------|----------------|
| **File-watcher / watch mode** | Drop a new `PROD-XXXX.json` file and the agent triages it automatically — this is the "always-on" part of the name |
| **Streaming output** | Reasoning streams word-by-word to the terminal — dramatically more impressive live and faster to act on |
| **Prompt caching** | Policy and contracts cached across runs — ~90% cost reduction on repeated audit runs |
| **Eval harness** | Automated assertions on known correlations — prevents prompt regressions as you iterate |

### Next Phase — Connect to your actual stack (P2)

| Feature | What it unlocks |
|---------|----------------|
| **Live incident feed** | Replace synthetic JSON with PagerDuty or Jira webhooks — real incidents, real-time |
| **Slack / Teams notification** | Agent routes findings directly to your on-call channel instead of writing a file |
| **Multi-agent architecture** | Specialist triage agent + specialist audit agent orchestrated by a router — parallel analysis, faster results |
| **Human-in-the-loop for P0s** | Agent proposes action, human approves before execution — safe automation at the sharp end |
| **Persistent memory** | Agent remembers prior triage findings and doesn't re-investigate incidents it already closed |

### 6-Month Vision

An always-on enterprise ops intelligence layer that continuously monitors incident feeds, deploy pipelines, and contract repositories. It proactively surfaces risk before humans notice. It generates and routes remediation tickets. It becomes the connective tissue between on-call, legal, and engineering — the institutional memory that doesn't go home at 5pm.

The path from here to there is linear: **MVP proves the reasoning works → P1 proves it works in real-time → P2 proves it integrates with the stack you already have.**

---

*Always-On Ops Agent — built at the BTS AI Hackathon, May 2026*
