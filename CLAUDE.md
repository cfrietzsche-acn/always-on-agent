# CLAUDE.md — Always-On Ops Agent

This file is read automatically by Claude Code on every session. It is the single source of truth for project context, build instructions, and technical decisions. Do not deviate from the structure or patterns defined here without explicit instruction.

---

## What this project is

An always-on enterprise ops agent built on top of a synthetic data repository. The agent runs two autonomous modes — **triage** and **audit** — using a standard Anthropic tool-use loop. It reads structured data files (incidents, deploys, runbooks, contracts, compliance policy), reasons across them, and writes markdown reports. No database. No external APIs beyond Anthropic.

The demo value: the agent discovers cross-incident correlations and contract violations that a human would spend 45–120 minutes finding manually. It does this in under 90 seconds, with reasoning visible in the terminal.

---

## Repository layout

```
always-on-agent/               ← repo root
├── issues/                    ← 5 PROD incidents as JSON
│   ├── PROD-4487.json
│   ├── PROD-4498.json
│   ├── PROD-4506.json
│   ├── PROD-4519.json
│   └── PROD-4521.json
├── runbooks/                  ← 3 markdown diagnostic guides
├── contracts/                 ← 3 vendor contracts (Acme, Globex, Sirius)
├── deploys/
│   └── recent.json            ← 5 recent microservice deploys
├── compliance-policy.md       ← 8 vendor compliance rules
├── CLAUDE.md                  ← this file
├── product-management/        ← all product and project management artifacts
│   ├── TENETS.md              ← agent operating principles
│   ├── DESIGN.md              ← full design specification
│   ├── ROADMAP.md             ← 60-minute build plan + P1/P2
│   ├── skills/
│   │   ├── pm.md              ← product manager skill
│   │   ├── sdm.md             ← SDM + lead dev skill
│   │   └── qa.md              ← QA reviewer skill
│   └── issues/                ← sprint issue docs (issue-{name}-XX.md)
│       └── README.md          ← issue index + naming convention
└── agent/                     ← ALL new code lives here
    ├── main.py                ← CLI entrypoint
    ├── agent.py               ← tool-use loop
    ├── tools.py               ← 9 tools + TOOL_SCHEMAS + dispatch()
    ├── prompts.py             ← TRIAGE_SYSTEM + AUDIT_SYSTEM constants
    ├── requirements.txt       ← anthropic>=0.30.0
    └── reports/               ← created at runtime by write_report tool
```

**Rule:** All new code goes in `agent/`. The data files (`issues/`, `runbooks/`, `contracts/`, `deploys/`, `compliance-policy.md`) are read-only fixtures — never modify them.

---

## Sprint workflow

Every feature follows this loop. Nothing gets built without an issue doc; nothing gets pushed without a QA pass.

```
PM creates issue doc
        ↓
SDM reviews + adds tech verdict
        ↓
Dev implements + runs verification gates
        ↓
QA reviews diff vs. acceptance criteria
        ↓   Pass → git push origin main
        ↓   Fail → back to Dev
        ↓
Loop
```

### Skills dispatch

| Skill file | Invoke when... |
|------------|---------------|
| `product-management/skills/pm.md` | "pm review", "plan sprint", "next issue", "create an issue for X" |
| `product-management/skills/sdm.md` | "sdm review", "tech review", "ready to build", "build issue-X" |
| `product-management/skills/qa.md` | "qa review", "review before push", "ready to push", "qa on issue-X" |

**Rule:** Load the skill file before acting in that role. Do not invent behavior not defined in the skill file.

---

## Build this in order

Follow this sequence exactly. Each step has a verification gate before moving on.

### Step 1 — tools.py (target: 15 min)

Implement all 9 tools, `TOOL_SCHEMAS`, and `dispatch()`.

| Tool | Signature | Notes |
|------|-----------|-------|
| `list_issues` | `() → list[dict]` | Glob `issues/*.json`, return summary dicts: id, title, severity, opened_at, labels, status |
| `read_issue` | `(issue_id: str) → dict` | Full JSON for one issue file |
| `list_deploys` | `() → list[dict]` | All of `deploys/recent.json`, sorted newest-first by `deployed_at` |
| `list_runbooks` | `() → list[str]` | Filenames only |
| `search_runbook` | `(name: str) → str` | Full markdown content |
| `list_contracts` | `() → list[str]` | Filenames only |
| `read_contract` | `(name: str) → str` | Full markdown content |
| `read_compliance_policy` | `() → str` | Full `compliance-policy.md` |
| `write_report` | `(filename: str, content: str) → str` | Writes to `agent/reports/`, returns path |

`TOOL_SCHEMAS` is a list of Anthropic API tool dicts (name, description, input_schema). `dispatch(name, input_data)` routes to the correct function and always returns a string (serialize dicts/lists with `json.dumps`).

`REPO_ROOT` is a module-level variable set by `agent.py` at startup — do not hardcode the path.

**Verification gate:**
```bash
cd agent
python -c "import tools; tools.REPO_ROOT='..'; print(tools.list_issues())"
python -c "import tools; tools.REPO_ROOT='..'; print(tools.list_deploys())"
python -c "import tools; tools.REPO_ROOT='..'; print(tools.read_compliance_policy()[:200])"
```
All must return data, no errors. Do not proceed until this passes.

---

### Step 2 — prompts.py (target: 10 min)

Two system prompt constants: `TRIAGE_SYSTEM` and `AUDIT_SYSTEM`.

**TRIAGE_SYSTEM must instruct the agent to:**
1. List all issues
2. For each issue: read full body, then call `list_deploys` and identify any deploy within 48 hours prior to `opened_at`
3. Find and read the matching runbook for each affected service
4. Produce a structured finding per issue: severity (P0–P3), root cause hypothesis, contributing deploy (service + version + timestamp), recommended fix (specific, not generic), rollback availability
5. Flag PROD-4498 explicitly if no rollback is available — elevated risk
6. Write the final report via `write_report` with filename `triage-YYYY-MM-DD.md`

**AUDIT_SYSTEM must instruct the agent to:**
1. Read compliance policy in full first
2. List and read every contract
3. Evaluate each contract against all 8 policy rules
4. Per violation: vendor name, rule violated, quoted contract clause, risk level (Critical / High / Medium / Low), remediation recommendation
5. Produce an executive summary table: vendor | violation count | highest risk level | status
6. Write the final report via `write_report` with filename `compliance-audit-YYYY-MM-DD.md`

**Prompt engineering rules (non-negotiable):**
- Both prompts must say: "Do not write the report until you have read every relevant file."
- Both prompts must say: "Every finding must cite the specific file, field, or line that supports it."
- Both prompts must say: "Today's date is {date} — use this for all timestamp calculations."
- Triage prompt must say: "The deploy correlation window is 48 hours prior to `opened_at`."
- Audit prompt must say: "Treat any policy rule with no defined timeline or threshold as a Critical violation."

**No verification gate** — prompts are validated by Step 3.

---

### Step 3 — agent.py (target: 10 min)

Standard Anthropic tool-use loop.

```python
def run(mode: str, repo_root: str, model: str = "claude-sonnet-4-6"):
    tools.REPO_ROOT = repo_root
    system = TRIAGE_SYSTEM if mode == "triage" else AUDIT_SYSTEM
    system = system.replace("{date}", datetime.date.today().isoformat())

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Run the {mode} workflow now."}]

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Print final text block
            for block in response.content:
                if hasattr(block, "text"):
                    print(block.text)
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → {block.name}({block.input})")
                    result = dispatch(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            # CRITICAL: all tool results go in ONE user message
            messages.append({"role": "user", "content": tool_results})
```

**The single most common failure mode:** tool results must go into a `user`-role message as an **array** of `tool_result` content blocks. Not a separate `assistant` message. Not one message per result. One `user` message containing all results for that turn.

**Verification gate:**
```bash
python -c "
import agent, os
os.environ['ANTHROPIC_API_KEY'] = 'your-key'
# Minimal smoke test — single tool call
"
python main.py triage
# Should stream tool calls and complete without error
```

---

### Step 4 — main.py (target: 5 min)

```python
#!/usr/bin/env python3
import sys, os, pathlib

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("triage", "audit"):
        print("Usage: python main.py [triage|audit]")
        sys.exit(1)
    mode = sys.argv[1]
    repo_root = str(pathlib.Path(__file__).parent.parent.resolve())
    from agent import run
    print(f"\n[agent] Starting {mode} mode — repo: {repo_root}\n")
    run(mode, repo_root)

if __name__ == "__main__":
    main()
```

---

### Step 5 — end-to-end test (target: 10 min)

```bash
cd always-on-agent/agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python main.py triage
# Verify: reports/triage-2026-05-27.md exists and contains all 5 issue IDs

python main.py audit
# Verify: reports/compliance-audit-2026-05-27.md exists and Sirius has ≥4 Critical violations
```

**Known ground truth — check these manually:**

| Check | Expected |
|-------|----------|
| PROD-4487 + PROD-4521 root cause | Same — payment-service v4.8.2 NPE at `PaymentService.java:142` |
| PROD-4487 + PROD-4521 trigger | guest-checkout feature flag enabled for Acme Corp cohort |
| PROD-4519 root cause | signing-service v2.1.4 reduced `URL_TTL_SECONDS` from 3600→300 |
| PROD-4498 flag | No rollback available — elevated risk, do not attempt rollback |
| Sirius Storage violations | ≥4 Critical (data residency, termination, liability cap, breach notification) |
| Globex | Compliant — zero violations |
| Acme Data Platform | ~4 violations, lower severity |

If any check fails, iterate on the system prompt for that mode before touching code.

---

## Critical technical decisions

**Model:** `claude-sonnet-4-6` — do not use Opus or Haiku for this build.

**Max tokens:** 8192 — the triage report is long. Do not lower this.

**No streaming in MVP** — use `client.messages.create`, not `client.messages.stream`. Streaming is a P1 stretch goal.

**Tool result format** — always a string. `dispatch()` must serialize everything to string before returning.

**REPO_ROOT** — always resolved at startup from `main.py` as the parent of the `agent/` directory. Never hardcoded.

**reports/ directory** — created by `write_report` if it doesn't exist (`os.makedirs(..., exist_ok=True)`).

---

## What not to build in this session

- No file-watcher / watch mode
- No streaming output
- No cross-mode "full" report
- No eval harness
- No external API integrations
- No UI beyond terminal print statements
- No database

These are P1 and P2 items. See ROADMAP.md.

---

## Environment setup

The API key lives in `.env` at the repo root (already gitignored). The key name in that file is `api_key` (not `ANTHROPIC_API_KEY`). `main.py` loads it at startup via `python-dotenv` and passes it explicitly to the Anthropic client.

**Do not export `ANTHROPIC_API_KEY` manually — the .env handles it.**

```bash
# From repo root — system Python is externally managed (PEP 668); use a venv
python3 -m venv .venv
.venv/bin/pip install -r agent/requirements.txt

# Run the agent
cd agent
../.venv/bin/python main.py triage
../.venv/bin/python main.py audit
```

The `.env` load pattern in `main.py`:
```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")
api_key = os.environ.get("api_key")
```

And passed to the client in `agent.py`:
```python
client = anthropic.Anthropic(api_key=api_key)
```

`api_key` is passed as a parameter from `main.py` → `run()` — not read from the environment inside `agent.py`.
