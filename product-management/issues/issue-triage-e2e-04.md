# Issue: Validate Triage Mode End-to-End

**ID:** issue-triage-e2e-04
**Date:** 2026-05-27
**Status:** Draft → SDM Review

---

## Problem Statement

The agent loop runs but we don't know if the triage report surfaces the known correlations. The demo depends on the agent discovering the PROD-4487/4521 root cause and the PROD-4519 deploy link without being told what to look for. This sprint validates that and iterates on `TRIAGE_SYSTEM` until the ground truth passes.

## User Story

As a demo presenter, I want the triage report to autonomously surface all known incident-deploy correlations so that I can show the audience a correct, specific, cited report and say "no rules were written — the agent reasoned to this."

## Acceptance Criteria

- [ ] `python main.py triage` completes without error or uncaught exception
- [ ] `agent/reports/triage-YYYY-MM-DD.md` is written after the run
- [ ] Report contains all 5 issue IDs (PROD-4487, PROD-4498, PROD-4506, PROD-4519, PROD-4521)
- [ ] PROD-4487 and PROD-4521 are identified as sharing the same root cause (payment-service v4.8.2, NPE at `PaymentService.java:142`)
- [ ] The trigger for PROD-4487/4521 is identified as the guest-checkout feature flag rollout to Acme Corp cohort (tenant-config-service v3.2.1, 2026-05-20 07:12 UTC)
- [ ] PROD-4519 root cause is identified as signing-service v2.1.4 reducing `URL_TTL_SECONDS` from 3600s to 300s
- [ ] PROD-4498 flags that auth-service v6.0.0 has no rollback available, and treats this as elevated risk — not buried as a footnote
- [ ] PROD-4506 is classified as a feature request / enhancement (P3 or equivalent) with no deploy correlation
- [ ] Each finding cites a specific file, field, or timestamp (not a paraphrase)

## Out of Scope

- Automated eval harness with programmatic assertions (P1)
- Changing any data files in `issues/`, `runbooks/`, or `deploys/`
- Changing `tools.py` or `agent.py` unless a tool bug is discovered
- Streaming output (P1)

---

## SDM Technical Review

**Verdict:** [x] Go

**Approach:**
This is a prompt engineering sprint, not a code sprint. The workflow is: run `python main.py triage` → open the generated report → compare each finding against the ground truth table → if a correlation is missing or wrong, update `TRIAGE_SYSTEM` in `prompts.py` and re-run. Repeat until all acceptance criteria pass.

Do not touch `tools.py` or `agent.py` unless you observe a tool returning wrong data. Changes are to `prompts.py` only.

Iteration order if findings fail:
1. **If PROD-4487/4521 don't correlate:** The agent likely didn't read both issue bodies before concluding, or didn't correlate deploy timestamps. Strengthen: "Before writing any finding, verify whether any other open issue shares the same affected service. If yes, read that issue too and determine if they share a root cause."
2. **If PROD-4519 deploy link is missing:** The agent likely didn't match the signing-service deploy to the upload latency pattern. Strengthen: "For each issue, compare the `opened_at` timestamp to all deploys within the 48-hour window. List the matching deploys explicitly before forming a hypothesis."
3. **If PROD-4498 rollback risk is buried:** Strengthen: "If `rollback_available` is false for a contributing deploy, this MUST appear as the first line of the finding under ROLLBACK STATUS, not in the recommendation text."
4. **If PROD-4506 is over-classified:** Ensure the severity definitions in the prompt distinguish customer-facing impact from engineering requests.

Each iteration of `TRIAGE_SYSTEM` should be committed separately with the report file as evidence.

**Risks / gotchas:**
- The 14-minute gap between the payment-service deploy (14:04 UTC) and the NPE alert (14:18 UTC) is the key timestamp the agent must connect. If it misses this, the 48h window instruction is correct but the agent isn't reading timestamps carefully enough — add an explicit instruction: "Calculate the delta in minutes between the deploy `deployed_at` and the issue `opened_at`."
- The tenant-config-service feature flag deploy is the second contributing factor for PROD-4487. The agent needs to read both the payment-service deploy AND the tenant-config deploy to get the full picture. It may find only one — that's a partial credit finding, not a failure, but note it.

---

## Dev Notes

> To be filled during implementation.

---

## QA Sign-Off

> To be filled before GitHub push.

**Verdict:** [ ] Pass  [ ] Fail
**Findings:**
