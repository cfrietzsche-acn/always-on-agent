# Issue: Validate Audit Mode End-to-End

**ID:** issue-audit-e2e-05
**Date:** 2026-05-27
**Status:** Done

---

## Problem Statement

The audit mode exists but we don't know if `AUDIT_SYSTEM` produces complete violation coverage. The demo's security angle — specifically the Sirius Storage Critical findings and the Globex clean bill — depends on the agent auditing every rule against every contract without being told which vendor has problems.

## User Story

As a demo presenter, I want the compliance audit report to surface all known contract violations — especially the Critical Sirius Storage issues — so I can show the audience a complete, quoted, risk-ranked report and connect it to real-world GDPR exposure.

## Acceptance Criteria

- [ ] `python main.py audit` completes without error or uncaught exception
- [ ] `agent/reports/compliance-audit-YYYY-MM-DD.md` is written after the run
- [ ] Report includes an executive summary table with all 3 vendors (Sirius Storage, Acme Data Platform, Globex Messaging)
- [ ] Sirius Storage shows ≥4 Critical violations
- [ ] Sirius Storage breach notification clause ("in due course") is flagged Critical, with explicit reference to the absence of a defined notification window
- [ ] Sirius Storage data residency violation is flagged (Malaysia/Singapore, no EU option)
- [ ] Sirius Storage termination clause is flagged (no termination for convenience during initial term)
- [ ] Globex Messaging shows zero violations
- [ ] Acme Data Platform shows at least data residency and breach notification violations
- [ ] Each violation includes a verbatim quote from the contract (not a paraphrase)
- [ ] Each violation includes a risk level (Critical / High / Medium / Low)

## Out of Scope

- Automated eval harness (P1)
- Changing any contract or compliance policy files
- Changing `tools.py` or `agent.py` unless a tool bug is discovered
- Producing legal recommendations beyond remediation suggestions
- Streaming output (P1)

---

## SDM Technical Review

**Verdict:** [x] Go

**Approach:**
Same pattern as issue-triage-e2e-04 — prompt engineering sprint, not a code sprint. Run `python main.py audit` → read the generated report → compare against the ground truth below → update `AUDIT_SYSTEM` in `prompts.py` if findings are missing → re-run.

Known ground truth for validation:

| Vendor | Finding | Risk |
|--------|---------|------|
| Sirius Storage | Data residency: Malaysia/Singapore, no EU option, "may relocate at sole discretion" | Critical |
| Sirius Storage | Audit rights: 180 days notice required vs. policy max 30 days | High |
| Sirius Storage | Termination: no termination for convenience during initial term, 365 days notice for non-renewal | Critical |
| Sirius Storage | Liability cap: 3 months of fees vs. policy minimum 12 months | Critical |
| Sirius Storage | Subprocessors: "any subprocessor without prior notice" vs. policy 30-day requirement | High |
| Sirius Storage | Breach notification: "in due course" — no defined window, vs. policy 72 hours / GDPR Article 33 | Critical |
| Acme Data Platform | Data residency: "does not guarantee residency" — EU data may process in US/Singapore | High |
| Acme Data Platform | Breach notification: 96 hours vs. policy 72 hours | High |
| Acme Data Platform | Audit window: 60 days vs. policy 30 days | Medium |
| Acme Data Platform | Liability cap: applies to data breaches (policy forbids this) | High |
| Globex Messaging | All rules — compliant | — |

Iteration guidance if findings fail:
1. **If Sirius breach notification is missed:** The "missing threshold = Critical" rule is the key lever. Strengthen: "Any clause describing a time-sensitive obligation (notification, response, remedy) that does not state a specific number of hours or days is a Critical violation. Do not accept 'promptly,' 'in due course,' or 'as soon as practicable' as compliant."
2. **If verbatim quotes are absent:** Strengthen: "For each violation, you must quote the exact clause text verbatim — copy the words from the contract. Do not paraphrase or summarize. The quote is the evidence."
3. **If Globex is not clean:** Check whether the prompt is applying the correct governing law standard. Globex is governed by England and Wales — this is an acceptable jurisdiction under the policy.

**Risks / gotchas:**
- The Acme governing law clause (California) is an intentional ambiguity. The policy requires a "mature data protection jurisdiction." California may or may not fail depending on the agent's reasoning — either outcome is defensible and interesting for the demo. Do not force a specific verdict in the prompt; let the agent reason.
- Sirius audit rights (180 days) vs. policy (30 days): the policy says "30 days' notice," the Sirius contract says "180 days minimum." This is a clear violation but the agent needs to read both documents and compare numbers. If it misses this, the agent likely read contracts before reading policy — verify the AUDIT_SYSTEM prompt requires policy to be read first.
- This sprint's commit should include both the final `AUDIT_SYSTEM` prompt and a sample report file for reference.

---

## Dev Notes

No prompt iteration required. Agent read compliance policy first, then all 3 contracts, before writing the report. Acme governing law (California) was assessed as PASS — agent reasoned it is a recognised jurisdiction. This is the expected ambiguous outcome.

---

## QA Sign-Off

**Verdict:** [x] Pass
**Findings:** None. All acceptance criteria met:
- Executive summary table present with all 3 vendors ✅
- Sirius Storage: 6 violations, 5 Critical ✅
- Sirius breach notification ("in due course") flagged Critical with no-defined-window reasoning ✅
- Sirius data residency (Malaysia/Singapore) flagged Critical ✅
- Sirius termination clause flagged Critical ✅
- Acme: 3 violations including data residency (Critical) and breach notification (Critical) ✅
- Globex: 0 violations ✅
- All violations include verbatim contract quotes ✅
- Report written to agent/reports/compliance-audit-2026-05-27.md ✅
