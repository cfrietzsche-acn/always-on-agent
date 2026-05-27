#!/usr/bin/env python3
"""
Flask web UI for the Always-On Ops Agent demo.

Run from the repo root:
    .venv/bin/python agent/app.py
Then open http://localhost:5000
"""
import datetime
import glob
import json
import os
import pathlib
import queue
import sys
import threading

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, stream_with_context

AGENT_DIR = pathlib.Path(__file__).parent
REPO_ROOT = AGENT_DIR.parent

sys.path.insert(0, str(AGENT_DIR))

load_dotenv(REPO_ROOT / ".env")
API_KEY = os.environ.get("api_key")

app = Flask(__name__)


# ── Data routes ────────────────────────────────────────────────────────────────

@app.route("/api/issues")
def api_issues():
    paths = sorted(glob.glob(str(REPO_ROOT / "issues/PROD-*.json")))
    return jsonify([json.loads(pathlib.Path(p).read_text()) for p in paths])


@app.route("/api/deploys")
def api_deploys():
    data = json.loads((REPO_ROOT / "deploys/recent.json").read_text())
    return jsonify(data.get("deploys", []))


@app.route("/api/runbooks")
def api_runbooks():
    paths = sorted(glob.glob(str(REPO_ROOT / "runbooks/*.md")))
    return jsonify([
        {"name": pathlib.Path(p).stem, "content": pathlib.Path(p).read_text()}
        for p in paths
    ])


@app.route("/api/contracts")
def api_contracts():
    paths = sorted(glob.glob(str(REPO_ROOT / "contracts/*.md")))
    return jsonify([
        {"name": pathlib.Path(p).stem, "content": pathlib.Path(p).read_text()}
        for p in paths
    ])


@app.route("/api/policy")
def api_policy():
    return jsonify({"content": (REPO_ROOT / "compliance-policy.md").read_text()})


@app.route("/api/reports")
def api_reports():
    paths = sorted(glob.glob(str(AGENT_DIR / "reports/*.md")), reverse=True)
    return jsonify([
        {"name": pathlib.Path(p).name, "content": pathlib.Path(p).read_text()}
        for p in paths
    ])


# ── Agent streaming ────────────────────────────────────────────────────────────

def _agent_thread(mode, q):
    try:
        import anthropic
        import tools as tools_module
        from tools import TOOL_SCHEMAS, dispatch
        from prompts import AUDIT_SYSTEM, TRIAGE_SYSTEM

        tools_module.REPO_ROOT = str(REPO_ROOT)
        system = TRIAGE_SYSTEM if mode == "triage" else AUDIT_SYSTEM
        system = system.replace("{date}", datetime.date.today().isoformat())

        client = anthropic.Anthropic(api_key=API_KEY)
        messages = [{"role": "user", "content": f"Run the {mode} workflow now."}]

        while True:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=system,
                tools=TOOL_SCHEMAS,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    q.put({"type": "text", "content": text})
                response = stream.get_final_message()

            q.put({"type": "text", "content": "\n"})
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        q.put({"type": "tool", "name": block.name,
                               "input": str(block.input)[:120]})
                        result = dispatch(block.name, block.input)
                        q.put({"type": "result",
                               "preview": result[:100].replace("\n", " ")})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "user", "content": tool_results})

        today = datetime.date.today().isoformat()
        prefix = f"triage-{today}" if mode == "triage" else f"compliance-audit-{today}"
        reports = sorted(glob.glob(str(AGENT_DIR / f"reports/{prefix}*.md")), reverse=True)
        report = pathlib.Path(reports[0]).name if reports else None
        q.put({"type": "done", "report": report})

    except Exception as e:
        q.put({"type": "error", "message": str(e)})
    finally:
        q.put(None)


@app.route("/stream/<mode>")
def stream_agent(mode):
    if mode not in ("triage", "audit"):
        return "Invalid mode", 400
    if not API_KEY:
        return "API key not configured — check .env", 500

    q = queue.Queue()
    threading.Thread(target=_agent_thread, args=(mode, q), daemon=True).start()

    def generate():
        while True:
            item = q.get()
            if item is None:
                yield 'data: {"type":"end"}\n\n'
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print(f"\n[ui] Always-On Ops Agent")
    print(f"[ui] Repo:    {REPO_ROOT}")
    print(f"[ui] API key: {'✓ loaded' if API_KEY else '✗ MISSING'}")
    print(f"[ui] Open:    http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
