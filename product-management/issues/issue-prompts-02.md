# Issue: Write System Prompts for Triage and Audit Modes

**ID:** issue-prompts-02
**Date:** 2026-05-27
**Status:** Done

---

## Problem Statement

The tools exist but the agent has no reasoning instructions. Without `TRIAGE_SYSTEM` and `AUDIT_SYSTEM`, the tool-use loop has no idea what to do with the data it can read. Prompt quality directly determines whether the agent surfaces the known correlations that make the demo work.

## User Story

As the agent runtime, I want precise system prompts that tell me exactly how to reason about incidents and contracts so that I produce structured, cited, traceable reports without being told what to look for on each run.

## Acceptance Criteria

- [ ] `agent/prompts.py` exports two string constants: `TRIAGE_SYSTEM` and `AUDIT_SYSTEM`
- [ ] Both prompts contain `{date}` as a placeholder (not today's date hardcoded — injected at runtime)
- [ ] Both prompts include the instruction: "Do not write the report until you have read every relevant file."
- [ ] Both prompts include the instruction: "Every finding must cite the specific file, field, or line that supports it."
- [ ] `TRIAGE_SYSTEM` explicitly defines the deploy correlation window as 48 hours prior to `opened_at`
- [ ] `TRIAGE_SYSTEM` includes P0–P3 severity definitions
- [ ] `TRIAGE_SYSTEM` includes the rollback-unavailable escalation rule
- [ ] `AUDIT_SYSTEM` instructs the agent to read compliance policy before reading any contract
- [ ] `AUDIT_SYSTEM` includes the rule: "Any contract clause with no defined timeline or threshold is a Critical violation."
- [ ] Both prompts end with an explicit instruction to call `write_report` as the final step

## Out of Scope

- Cross-mode "full" report prompt (P1)
- Streaming-aware prompt variations (P1)
- Per-incident severity overrides or dynamic prompt injection
- Prompt versioning or A/B variants

---

## SDM Technical Review

**Verdict:** [x] Go

**Approach:**
Two module-level string constants in `prompts.py`. No imports required. Date injection happens in `agent.py` at runtime via `system.replace("{date}", datetime.date.today().isoformat())` — prompts.py has no runtime logic.

Prompt structure for `TRIAGE_SYSTEM`:
1. Role definition (always-on ops agent)
2. Severity scale (P0 = customer data loss or full outage; P1 = major customer impact; P2 = degraded service; P3 = no customer impact)
3. Workflow instructions (list → read each → check deploys → find runbook → conclude)
4. Deploy correlation rule (48h window, cite service + version + timestamp delta)
5. Rollback escalation rule (flag prominently if `rollback_available: false`)
6. Output structure per incident (ID, severity, root cause, contributing deploy, recommended fix, rollback status, cross-issue correlation if found)
7. "Read before concluding" and "cite specifically" mandates
8. Final instruction: call `write_report("triage-{date}.md", ...)`

Prompt structure for `AUDIT_SYSTEM`:
1. Role definition (compliance auditor)
2. Workflow instructions (policy first → list contracts → read each → evaluate every rule)
3. Missing-threshold rule (any vague obligation = Critical)
4. Output structure per violation (vendor, rule violated, verbatim quote, risk level, remediation)
5. Executive summary table requirement (vendor | violations | highest risk | status)
6. "Read before concluding" and "cite specifically" mandates
7. Final instruction: call `write_report("compliance-audit-{date}.md", ...)`

**Risks / gotchas:**
- Prompt quality is not verifiable until Issues 03 and 04/05 run end-to-end. Expect iteration on both prompts during those sprints — this issue is about getting the structure right, not perfecting the output.
- The most common failure mode: agent reads the issue list summary and writes a report without calling `read_issue` on each. The "read before concluding" instruction is the primary defense. If it fails in E2E testing, strengthen it with "you must call read_issue for every issue ID before forming any hypothesis."
- The Acme governing law clause (California) is an intentional ambiguity in the data — either outcome in the audit is acceptable. Do not try to force a specific verdict in the prompt.

---

## Dev Notes

`TRIAGE_SYSTEM` and `AUDIT_SYSTEM` implemented as module-level string constants. Both use `{date}` placeholder replaced at runtime via `system.replace("{date}", datetime.date.today().isoformat())` in `agent.py`. No imports in `prompts.py`. Both prompts validated end-to-end in issues 04 and 05.

---

## QA Sign-Off

**Verdict:** [x] Pass
**Findings:** None. Both prompts validated by running both modes end-to-end (issues 04 and 05). All ground truth findings surfaced on first run without prompt iteration.
