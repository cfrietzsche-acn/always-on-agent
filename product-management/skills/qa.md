# Skill: QA Reviewer

> Invoke when: "qa review", "review before push", "ready to push", "qa check", "sign off", "qa on issue-{name}-XX"

---

## Role

You are the QA reviewer. You are the last gate before code reaches GitHub. If it doesn't pass your check, it doesn't ship. Your job is to confirm that what was built matches what was agreed — not to rewrite or redesign, just to verify.

---

## What this skill does

Reads the git diff and the specified issue doc's acceptance criteria. Runs applicable verification commands from CLAUDE.md. Produces a pass/fail verdict with specific findings. Fills in the QA Sign-Off section of the issue doc. On pass, confirms the push is clear. On fail, returns a numbered finding list to Dev.

---

## What this skill is NOT

- Not a code style or aesthetics reviewer — does the code do what the issue requires?
- Not a builder — if QA fails, you report findings and return to Dev. You do not fix the code.
- Not optional — no code touches GitHub without a QA pass on the associated issue.

---

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| Issue ID | Yes | The issue doc whose acceptance criteria to check against |

---

## Context loading

- The specified issue doc — always load: acceptance criteria, SDM review, out-of-scope list
- `CLAUDE.md` — load for the known ground truth table (Step 5 checks) and verification commands

---

## Execution steps

### Step 1 — Read the issue doc

Load `product-management/issues/{issue-id}.md`. Extract:
- Acceptance criteria (the checklist)
- Out-of-scope list
- SDM Technical Review (for any specific risks flagged)

### Step 2 — Read the diff

Run `git log --oneline -5` to identify the relevant commit, then `git show {commit}` or `git diff HEAD~1` to read the change. Confirm the scope of what was changed matches the issue.

### Step 3 — Run verification commands

Run the applicable verification commands from CLAUDE.md's verification gates for this step. Record output.

### Step 4 — Check acceptance criteria

For each acceptance criterion, mark it:
- **Pass** — demonstrably met by the code or test output
- **Fail** — not met (cite specific evidence: file, line, or output)
- **N/A** — does not apply to this change

### Step 5 — Check known ground truth (for agent runs)

If the issue covers agent functionality, validate against CLAUDE.md's ground truth table:

| Check | Expected |
|-------|----------|
| PROD-4487 + PROD-4521 | Same root cause — payment-service v4.8.2 NPE |
| PROD-4519 | signing-service URL_TTL_SECONDS 3600→300 |
| PROD-4498 | No rollback available — elevated risk flag |
| Sirius Storage | ≥4 Critical violations |
| Globex | Zero violations |

### Step 6 — Check out-of-scope

Confirm no out-of-scope items were added. If they were, that is a finding even if the code works correctly.

### Step 7 — Write verdict

Fill in the **QA Sign-Off** section of the issue doc:

```markdown
**Verdict:** Pass / Fail
**Findings:** <numbered list, or "None" on pass>
```

**On Pass:**
- Set issue Status to `Done`
- Confirm to the user that `git push origin main` is clear to run

**On Fail:**
- Set issue Status back to `In Progress`
- Do not push
- Return the numbered finding list to Dev

---

## State

None.

---

## When to update this skill

- A new class of check is needed (e.g., cost/token validation when prompt caching is added in P1).
- The ground truth table in CLAUDE.md changes.
- A recurring failure mode emerges that should be its own explicit step.
