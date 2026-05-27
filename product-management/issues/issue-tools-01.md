# Issue: Implement All Agent Tools

**ID:** issue-tools-01
**Date:** 2026-05-27
**Status:** Draft → SDM Review

---

## Problem Statement

The agent has no way to read from the repo. Without file I/O tools, the tool-use loop has nothing to call — every agent capability depends on this layer existing first.

## User Story

As a developer wiring up the agent loop, I want all 9 tools implemented with correct Anthropic API schemas so that the agent can read incidents, deploys, runbooks, contracts, and compliance policy — and write reports — without any hardcoded logic.

## Acceptance Criteria

- [ ] All 9 tools implemented in `agent/tools.py`
- [ ] `TOOL_SCHEMAS` is a list of 9 Anthropic API tool dicts (each with `name`, `description`, `input_schema`)
- [ ] `dispatch(name, input_data)` routes all 9 tool names correctly and returns a string for every call
- [ ] `REPO_ROOT` is a module-level variable set to `None` at import — never hardcoded
- [ ] All tools serialize non-string returns with `json.dumps` before returning
- [ ] `write_report` creates `agent/reports/` with `os.makedirs(..., exist_ok=True)` and returns the written path as a string
- [ ] Verification gate passes with no errors:
  ```bash
  python -c "import tools; tools.REPO_ROOT='..'; print(tools.list_issues())"
  python -c "import tools; tools.REPO_ROOT='..'; print(tools.list_deploys())"
  python -c "import tools; tools.REPO_ROOT='..'; print(tools.read_compliance_policy()[:200])"
  ```

## Out of Scope

- Streaming or async tool execution (P1)
- Retry logic or error recovery beyond basic `FileNotFoundError` handling (P1)
- Any tool not listed in DESIGN.md's tool contracts table
- Connecting to external APIs (this sprint is file I/O only)

---

## requirements.txt

`agent/requirements.txt` is created in this sprint with exactly:

```
anthropic>=0.30.0
python-dotenv>=1.0.0
```

`python-dotenv` is needed because the API key lives in `.env` at the repo root with the key name `api_key` (not `ANTHROPIC_API_KEY`). It must be loaded explicitly — the Anthropic SDK will not find it automatically.

---

## SDM Technical Review

**Verdict:** [x] Go

**Approach:**
Pure Python file I/O. All reads use `open(os.path.join(REPO_ROOT, ...))`. List tools use `glob.glob(...)`. `TOOL_SCHEMAS` is a plain Python list of dicts — no abstraction layer needed. `dispatch()` is a dict of lambdas keyed by tool name; unknown names return a JSON error string rather than raising.

Tool-by-tool signatures:
| Tool | Input | Implementation |
|------|-------|----------------|
| `list_issues` | none | `glob("issues/*.json")` → parse each → return summary dict array (id, title, severity, status, opened_at, labels) |
| `read_issue` | `issue_id: str` | `open(f"issues/{issue_id}.json")` → return raw file content |
| `list_deploys` | none | `open("deploys/recent.json")` → return array sorted newest-first by `deployed_at` |
| `list_runbooks` | none | `glob("runbooks/*.md")` → return filenames only |
| `search_runbook` | `name: str` | `open(f"runbooks/{name}.md")` → return full markdown |
| `list_contracts` | none | `glob("contracts/*.md")` → return filenames only |
| `read_contract` | `name: str` | `open(f"contracts/{name}.md")` → return full markdown |
| `read_compliance_policy` | none | `open("compliance-policy.md")` → return full markdown |
| `write_report` | `filename: str, content: str` | Write to `agent/reports/`, return confirmation string with full path |

**Risks / gotchas:**
- `dispatch()` must always return a string — the Anthropic API will error if it receives a dict or list. Wrap every return in `json.dumps()` or ensure it's already a string.
- `REPO_ROOT` must be set by `agent.py` before any tool is called. If a test imports `tools` directly, set `tools.REPO_ROOT = ".."` (relative to `agent/`) before calling anything.
- `list_issues` returns summaries, not full bodies — this keeps the initial listing lightweight. The agent must call `read_issue` to get full content.

---

## Dev Notes

> To be filled during implementation.

---

## QA Sign-Off

> To be filled before GitHub push.

**Verdict:** [ ] Pass  [ ] Fail
**Findings:**
