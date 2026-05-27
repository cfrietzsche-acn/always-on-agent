# DESIGN.md — Always-On Ops Agent

## Problem statement

On-call engineers face two recurring time sinks: triaging production incidents by manually correlating issues with recent deploys, and auditing vendor contracts against compliance policy before risk reviews. Both tasks are pattern-matching across structured data. Both take 45–120 minutes per cycle. Neither requires human judgment for the initial pass — they require thoroughness.

This agent performs both passes autonomously, in under 90 seconds each, and produces written reports that give humans a confirmed starting point instead of a blank page.

---

## Design goals

| Goal | Description |
|------|-------------|
| Autonomous | Runs a complete workflow end-to-end with no mid-run prompting |
| Traceable | Every finding cites a specific source file, field, or line |
| Fast | Both modes complete in under 90 seconds on the synthetic dataset |
| Durable | Outputs a written markdown report that persists after the run |
| Extensible | Adding a new mode requires only a new system prompt and optional new tools |

---

## Architecture

```
main.py  ──►  agent.py (tool-use loop)  ──►  tools.py (file I/O)
                    │                              │
                    │                        REPO_ROOT/
                    │                         issues/
                    │                         deploys/
                    │                         runbooks/
                    │                         contracts/
                    │                         compliance-policy.md
                    │
                    ▼
              agent/reports/
               triage-YYYY-MM-DD.md
               compliance-audit-YYYY-MM-DD.md
```

The loop is a standard Anthropic tool-use cycle: send messages → receive response → if `tool_use`, dispatch tools and append results as a `user` message → repeat until `end_turn`.

The agent is stateless between runs. All state lives in the messages array within a single run.

---

## The two modes

### Triage mode

**Trigger:** `python main.py triage`

**What the agent does:**
1. Calls `list_issues` — gets all 5 PROD incidents
2. For each incident, calls `read_issue` — gets full body including timestamps, labels, affected services
3. Calls `list_deploys` — checks for services deployed within 48 hours of each `opened_at`
4. Calls `list_runbooks` then `search_runbook` for the relevant service
5. Cross-correlates findings across issues (e.g. same service, same deploy window)
6. Produces a ranked report and calls `write_report`

**Output structure per incident:**
- Incident ID + title
- Severity (P0–P3 with rationale)
- Root cause hypothesis (specific, cited)
- Contributing deploy (service, version, timestamp delta to incident)
- Recommended fix (exact — code location, config key, feature flag name)
- Rollback availability (yes / no / elevated risk)
- Cross-incident correlation if applicable

**Known correlations the agent must surface:**

| Issues | Connection | Root cause |
|--------|-----------|------------|
| PROD-4487 + PROD-4521 | Same root cause | payment-service v4.8.2 — NPE at `PaymentService.java:142` triggered by guest-checkout feature flag for Acme Corp cohort |
| PROD-4519 | Deploy-correlated | signing-service v2.1.4 — `URL_TTL_SECONDS` reduced from 3600s → 300s causing S3 URL expiry before upload completes |
| PROD-4498 | Elevated risk | auth-service v6.0.0 — Redis migration, no rollback available |

---

### Audit mode

**Trigger:** `python main.py audit`

**What the agent does:**
1. Calls `read_compliance_policy` — reads all 8 rules in full
2. Calls `list_contracts` — gets all 3 vendor contract filenames
3. For each contract, calls `read_contract` — reads full text
4. Evaluates each contract against every policy rule
5. Produces per-vendor violation list and executive summary table
6. Calls `write_report`

**Output structure:**

Executive summary table:
```
| Vendor          | Violations | Highest Risk | Status        |
|-----------------|------------|--------------|---------------|
| Sirius Storage  | 6          | Critical     | Action needed |
| Acme Data Plat. | 4          | High         | Review needed |
| Globex          | 0          | —            | Compliant     |
```

Per violation:
- Vendor name
- Policy rule violated
- Quoted contract clause (verbatim excerpt)
- Risk level (Critical / High / Medium / Low)
- Remediation recommendation

**Known violations the agent must surface:**

| Vendor | Violations | Key Critical |
|--------|-----------|-------------|
| Sirius Storage | 6 total, 4 Critical | Data residency, termination clause, liability cap, breach notification ("in due course" — no defined window, GDPR Article 33 exposure) |
| Acme Data Platform | 4 total | Lower severity |
| Globex | 0 | Fully compliant |

---

## Tool contracts

All tools are pure file reads from `REPO_ROOT`. `write_report` is the only write operation. All tools return strings (dicts/lists serialized as JSON).

| Tool | Input | Return |
|------|-------|--------|
| `list_issues` | none | JSON array of summary dicts |
| `read_issue` | `issue_id: str` | JSON dict (full issue body) |
| `list_deploys` | none | JSON array, newest-first |
| `list_runbooks` | none | JSON array of filenames |
| `search_runbook` | `name: str` | Markdown string |
| `list_contracts` | none | JSON array of filenames |
| `read_contract` | `name: str` | Markdown string |
| `read_compliance_policy` | none | Markdown string |
| `write_report` | `filename: str, content: str` | Confirmation string with path |

---

## Context engineering decisions

| Decision | Rationale |
|----------|-----------|
| Today's date injected into system prompt | Agent needs it for 48h deploy correlation window calculation |
| Severity definitions in system prompt (P0–P3) | Standardizes output, prevents inconsistent labeling |
| Rollback risk rule in system prompt | Ensures PROD-4498 is flagged correctly without hard-coding |
| "Missing threshold = Critical" rule in audit prompt | Surfaces Sirius breach notification clause correctly |
| "Read everything before concluding" instruction | Prevents premature report generation after shallow tool calls |
| Deploy correlation window (48h) explicit in prompt | Agent would otherwise choose its own window arbitrarily |

---

## What this is not

- Not a real-time monitoring system (P1)
- Not connected to PagerDuty, Jira, or Slack (P2)
- Not multi-agent (P2)
- Not evaluated with automated fixture tests (P1)
- Not production-hardened (retry logic, rate limiting, cost controls)

See ROADMAP.md for what comes next.
