# ROADMAP.md — Build Plan + Future Roadmap

---

## 60-minute MVP build

The goal is a working demo of both modes with visible tool-call streaming in the terminal. Every time block has a hard stop and a kill decision.

```
00:00 ──────────────────────────────────────────────────────────── 60:00
  │                                                                    │
  ├── [00–15] tools.py                                                 │
  │   Build all 9 tools + TOOL_SCHEMAS + dispatch()                    │
  │   Gate: python -c verify each tool returns real data               │
  │   Kill: if gate fails at 15 min, drop search_runbook first         │
  │                                                                    │
  ├── [15–25] prompts.py                                               │
  │   Write TRIAGE_SYSTEM and AUDIT_SYSTEM                             │
  │   No verification gate — validated in the next step                │
  │   Kill: if running long, write triage prompt only                  │
  │                                                                    │
  ├── [25–35] agent.py + main.py                                       │
  │   Tool-use loop + CLI entrypoint                                   │
  │   Gate: python main.py triage runs without crashing                │
  │   Kill: if loop is broken at 35 min, check tool_result format      │
  │                                                                    │
  ├── [35–50] triage end-to-end                                        │
  │   Run full triage, verify ground truth against known correlations  │
  │   Iterate on TRIAGE_SYSTEM prompt until correlations surface       │
  │   Kill: if PROD-4487/4521 don't correlate by 50 min, freeze triage │
  │         and skip audit — one working mode beats two broken ones    │
  │                                                                    │
  ├── [50–57] audit end-to-end                                         │
  │   Run full audit, verify Sirius violations and Globex clean        │
  │   Iterate on AUDIT_SYSTEM prompt if needed                         │
  │                                                                    │
  └── [57–60] demo rehearsal                                           │
      Walk through demo script once. Know the two terminal commands.   │
      Know the three report lines you'll zoom in on.                   │
```

### Hard stops

- **15 min** — tools.py complete and verified. If not, you have a dependency problem, not a time problem. Debug before proceeding.
- **45 min** — triage mode must work. If it doesn't, stay on triage and cut audit.
- **57 min** — stop building. Rehearse.

### Kill decision tree

```
At 45 min:
  triage works? ──── yes ──► proceed to audit
                └── no  ──► fix prompt first, then audit only if time

At 55 min:
  both modes work? ── yes ──► clean up terminal output, rehearse
                  └── no  ──► demo only working mode, explain roadmap
```

---

## Demo script (10 minutes)

**Setup (30 sec):** Terminal open, repo visible, two commands ready.

**Act 1 — Triage (6 min):**
```
"This is what on-call sees at 3am — 5 open PROD incidents in JSON.
 No correlation, no context. Let's run the agent."

$ python main.py triage

[tool calls stream live]

"Watch what it's doing — it's reading every incident, pulling the deploy
 history, cross-referencing runbooks. No instructions from me."

[open reports/triage-2026-05-27.md]

"PROD-4487 and PROD-4521 — two separate ticket numbers, two separate
 alerts. The agent flagged them as the same root cause: payment-service
 v4.8.2, NPE at PaymentService.java:142, triggered by the guest-checkout
 feature flag for the Acme cohort. A deploy at 14:04, an alert at 14:18.
 The fix is one null check. That correlation took the agent 90 seconds.
 It takes an on-call engineer 45 minutes."
```

**Act 2 — Audit (3 min):**
```
"Same agent, different mode — vendor compliance."

$ python main.py audit

[open reports/compliance-audit-2026-05-27.md]

"Sirius Storage — 6 violations, 4 Critical. Look at this one:
 breach notification clause says 'in due course.' No defined window.
 GDPR Article 33 requires 72 hours. That clause is unenforceable
 and exposes the company to regulatory risk. The agent flagged it Critical.
 This is exactly what gets missed in a manual legal review."
```

**Close (30 sec):**
```
"90 seconds. Incident triage that takes 45 minutes on-call, and a contract
 review that takes a lawyer 2 hours — running on data already in your repo,
 no new infrastructure, no hard-coded rules. The agent figured it out."
```

---

## P1 — Production hardening (1–2 weeks)

These features make the demo into a real tool.

| Feature | Value | Effort |
|---------|-------|--------|
| Streaming output (`client.messages.stream`) | Reasoning streams word-by-word — dramatically more impressive live | 20 min |
| Prompt caching on policy + contracts | ~90% cost reduction on repeated audit runs | 20 min |
| File-watcher watch mode | Drop `PROD-XXXX.json` during demo, agent triages it live — this is the "always-on" proof | 60 min |
| Cross-mode `full` report | Runs triage + audit, then asks model to correlate — Acme appears as both impacted customer AND non-compliant vendor | 45 min |
| Eval harness with fixture tests | Assert known correlations appear in output — prevents prompt regressions | 2 hrs |
| Retry + error handling in loop | Production resilience — currently bare loop with no retry on API errors | 30 min |

---

## P2 — Real product (1–2 months)

These features turn this into enterprise infrastructure.

| Feature | Value | Effort |
|---------|-------|--------|
| Real incident feed (PagerDuty / Jira webhook) | Moves from synthetic data to live production incidents | 1 week |
| Slack / Teams notification tool | Agent routes findings directly to on-call channel | 3 days |
| Multi-agent architecture | Specialist triage agent + specialist audit agent orchestrated by a router agent | 2 weeks |
| Human-in-the-loop approval for P0 actions | Agent proposes action, human approves before execution | 1 week |
| Persistent memory across runs | Agent remembers prior triage findings, avoids re-investigating closed incidents | 1 week |
| Cost + latency observability | Per-run token counts, latency, tool call graph — needed before production | 3 days |

---

## 6-month vision

An always-on enterprise ops intelligence layer that continuously monitors incident feeds, deploy pipelines, and contract repositories. Proactively surfaces risk before humans notice. Generates and routes remediation tickets. Becomes the connective tissue between on-call, legal, and engineering — the institutional memory that doesn't go home at 5pm.

The path from here to there is linear: MVP proves the reasoning works → P1 proves it works in real-time → P2 proves it integrates with the stack you already have.
