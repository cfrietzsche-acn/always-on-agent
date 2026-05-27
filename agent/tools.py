import glob
import json
import os

REPO_ROOT = None


def list_issues():
    paths = sorted(glob.glob(os.path.join(REPO_ROOT, "issues/*.json")))
    summaries = []
    for p in paths:
        with open(p) as f:
            d = json.load(f)
        summaries.append({k: d.get(k) for k in ["id", "title", "severity", "status", "opened_at", "labels"]})
    return json.dumps(summaries, indent=2)


def read_issue(issue_id):
    path = os.path.join(REPO_ROOT, f"issues/{issue_id}.json")
    with open(path) as f:
        return f.read()


def list_deploys():
    path = os.path.join(REPO_ROOT, "deploys/recent.json")
    with open(path) as f:
        data = json.load(f)
    deploys = data.get("deploys", data) if isinstance(data, dict) else data
    deploys = sorted(deploys, key=lambda d: d.get("deployed_at", ""), reverse=True)
    return json.dumps(deploys, indent=2)


def list_runbooks():
    paths = sorted(glob.glob(os.path.join(REPO_ROOT, "runbooks/*.md")))
    return json.dumps([os.path.basename(p).replace(".md", "") for p in paths])


def search_runbook(name):
    path = os.path.join(REPO_ROOT, f"runbooks/{name}.md")
    with open(path) as f:
        return f.read()


def list_contracts():
    paths = sorted(glob.glob(os.path.join(REPO_ROOT, "contracts/*.md")))
    return json.dumps([os.path.basename(p).replace(".md", "") for p in paths])


def read_contract(name):
    path = os.path.join(REPO_ROOT, f"contracts/{name}.md")
    with open(path) as f:
        return f.read()


def read_compliance_policy():
    path = os.path.join(REPO_ROOT, "compliance-policy.md")
    with open(path) as f:
        return f.read()


def write_report(filename, content):
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, filename)
    with open(path, "w") as f:
        f.write(content)
    return f"Report written to {path}"


TOOL_DISPATCH = {
    "list_issues": lambda inp: list_issues(),
    "read_issue": lambda inp: read_issue(inp["issue_id"]),
    "list_deploys": lambda inp: list_deploys(),
    "list_runbooks": lambda inp: list_runbooks(),
    "search_runbook": lambda inp: search_runbook(inp["name"]),
    "list_contracts": lambda inp: list_contracts(),
    "read_contract": lambda inp: read_contract(inp["name"]),
    "read_compliance_policy": lambda inp: read_compliance_policy(),
    "write_report": lambda inp: write_report(inp["filename"], inp["content"]),
}


def dispatch(name, input_data):
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return fn(input_data)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


TOOL_SCHEMAS = [
    {
        "name": "list_issues",
        "description": "List all open production incidents. Returns a JSON array with id, title, severity, status, opened_at, and labels. Does NOT include the full body — call read_issue to get the full content of any incident.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_issue",
        "description": "Read the full content of a specific incident by ID (e.g. PROD-4487). Returns the complete JSON including body, timestamps, labels, and comments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_id": {"type": "string", "description": "The issue ID, e.g. PROD-4487"}
            },
            "required": ["issue_id"],
        },
    },
    {
        "name": "list_deploys",
        "description": "Return all recent deployments sorted newest-first. Includes service name, version, deployed_at timestamp, summary, files changed, and rollback_available status.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_runbooks",
        "description": "List the names of all available runbooks. Use search_runbook to read the full content of any runbook.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search_runbook",
        "description": "Read the full markdown content of a runbook by name (without .md extension), e.g. 'payment-service-degraded'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Runbook filename without .md, e.g. payment-service-degraded"}
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_contracts",
        "description": "List the names of all vendor contracts available for compliance audit.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_contract",
        "description": "Read the full markdown content of a vendor contract by name (without .md extension), e.g. 'sirius-storage'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Contract filename without .md, e.g. sirius-storage"}
            },
            "required": ["name"],
        },
    },
    {
        "name": "read_compliance_policy",
        "description": "Read the full internal vendor compliance policy. This defines the rules all vendor contracts must satisfy.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "write_report",
        "description": "Write the final analysis report to agent/reports/. Call this as the last step after all findings are complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "e.g. triage-2026-05-27.md"},
                "content": {"type": "string", "description": "Full markdown report content"},
            },
            "required": ["filename", "content"],
        },
    },
]
