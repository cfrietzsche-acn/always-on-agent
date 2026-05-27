# Issue: Implement Agent Loop and CLI Entrypoint

**ID:** issue-agent-loop-03
**Date:** 2026-05-27
**Status:** Draft → SDM Review

---

## Problem Statement

Tools and prompts exist but there is no orchestration layer — no loop that sends messages, handles tool calls, and drives the agent to completion. Without `agent.py` and `main.py`, the project cannot be run.

## User Story

As an operator, I want to run `python main.py triage` or `python main.py audit` and watch the agent call tools, reason across the data, and write a report — with each tool call visible in the terminal so the demo audience can follow along.

## Acceptance Criteria

- [ ] `agent/agent.py` exports a `run(mode, repo_root, api_key, model)` function
- [ ] The loop follows the pattern: send → receive → if `tool_use`, dispatch all tool calls and append results as one `user`-role message → if `end_turn`, print final text and break
- [ ] All tool results for a single turn are collected into one array and appended as one `user` message (never one message per result)
- [ ] Each tool call is logged to stdout: `  → {tool_name}({input})`
- [ ] `agent/main.py` accepts `triage` or `audit` as the subcommand; prints usage and exits for anything else
- [ ] `main.py` loads `.env` from the repo root: `load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")`
- [ ] `main.py` reads `api_key = os.environ.get("api_key")` after loading `.env` and exits with a clear error if missing or empty
- [ ] `main.py` resolves `REPO_ROOT` as the parent of the `agent/` directory using `pathlib.Path(__file__).parent.parent.resolve()`
- [ ] `main.py` creates `agent/reports/` at startup if it doesn't exist
- [ ] `agent.py` accepts `api_key` as a parameter and uses `anthropic.Anthropic(api_key=api_key)` — does not read from env directly
- [ ] `python main.py triage` runs to completion without an API error or uncaught exception
- [ ] A report file appears in `agent/reports/` after a successful run

## Out of Scope

- Streaming output (P1 — `client.messages.create`, not `client.messages.stream`)
- `--model` or `--repo-root` CLI flags (not needed for MVP)
- `watch` mode or file-watcher (P1)
- Retry logic on API errors (P1)
- Cross-mode `full` report (P1)

---

## SDM Technical Review

**Verdict:** [x] Go

**Approach:**
`agent.py` is a single `run()` function with the standard Anthropic tool-use loop. `main.py` is a thin CLI wrapper. The exact loop pattern is documented in CLAUDE.md — follow it without variation.

Critical message format rule (the single most common failure point for tool-use implementations):

```
After tool calls, append ONE user message containing ALL results:
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "...", "content": "..."},
    {"type": "tool_result", "tool_use_id": "...", "content": "..."},
    ...
]}

NOT one message per result. NOT an assistant-role message. ONE user message.
```

`main.py` env loading and REPO_ROOT resolution:
```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")
api_key = os.environ.get("api_key")
if not api_key:
    print("Error: api_key not found in .env"); sys.exit(1)
repo_root = str(pathlib.Path(__file__).parent.parent.resolve())
```
The `.env` at repo root uses the key name `api_key` (not `ANTHROPIC_API_KEY`). The Anthropic SDK does not auto-detect it — it must be passed explicitly. `api_key` is threaded through `run()` to `anthropic.Anthropic(api_key=api_key)`. No `export` command needed; no env var set in the shell.

Date injection in `agent.py`:
```python
system = system.replace("{date}", datetime.date.today().isoformat())
```
Run this before the first API call, not inside the loop.

**Risks / gotchas:**
- If the loop produces a `"messages must alternate user/assistant"` API error, the tool_results message is being appended as an assistant message or is being sent before the assistant response is appended. Check the order: (1) append assistant response, (2) collect all tool results, (3) append as one user message.
- `max_tokens=8192` is required — the triage report is long. Do not lower this.
- The loop must handle the case where `response.content` contains both text blocks and tool_use blocks in the same response. Iterate `response.content` and collect all `tool_use` blocks; text blocks in the same response are intermediate reasoning — print them if desired but don't stop the loop.

---

## Dev Notes

> To be filled during implementation.

---

## QA Sign-Off

> To be filled before GitHub push.

**Verdict:** [ ] Pass  [ ] Fail
**Findings:**
