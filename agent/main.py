#!/usr/bin/env python3
import glob
import os
import pathlib
import sys
import time

from dotenv import load_dotenv

VALID_MODES = ("triage", "audit", "watch", "generate", "demo")


def load_config():
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.environ.get("api_key")
    if not api_key:
        print(f"Error: 'api_key' not found in {env_path}")
        sys.exit(1)
    repo_root = str(pathlib.Path(__file__).parent.parent.resolve())
    reports_dir = pathlib.Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    return api_key, repo_root


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in VALID_MODES:
        print("Usage: python main.py [triage|audit|demo|watch|generate]")
        print()
        print("  triage    — triage all open incidents and write a report")
        print("  audit     — audit all vendor contracts and write a report")
        print("  demo      — run triage then audit back-to-back (full live demo)")
        print("  watch     — poll issues/ for new tickets and auto-triage each one")
        print("  generate  — drop a synthetic ticket into issues/ (use --loop to repeat)")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "generate":
        _, repo_root = load_config()
        from generator import generate, loop
        if "--loop" in sys.argv:
            interval = 60
            for i, arg in enumerate(sys.argv):
                if arg == "--interval" and i + 1 < len(sys.argv):
                    interval = int(sys.argv[i + 1])
            loop(repo_root, interval)
        else:
            generate(repo_root)
        return

    api_key, repo_root = load_config()

    if mode in ("triage", "audit"):
        from agent import run
        run(mode, repo_root, api_key)

    elif mode == "demo":
        _demo(api_key, repo_root)

    elif mode == "watch":
        _watch(api_key, repo_root)


def _banner(text: str):
    width = 60
    print("\n" + "─" * width)
    print(f"  {text}")
    print("─" * width + "\n")


def _demo(api_key: str, repo_root: str):
    import datetime
    from agent import run

    reports_dir = pathlib.Path(__file__).parent / "reports"
    today = datetime.date.today().isoformat()

    _banner("ACT 1 OF 2 — INCIDENT TRIAGE")
    print("  5 open PROD incidents. No assigned severity. No context.")
    print("  Watch the agent correlate across incidents, deploys, and runbooks.\n")
    run("triage", repo_root, api_key)
    triage_report = reports_dir / f"triage-{today}.md"
    if triage_report.exists():
        print(f"\n  Report written → {triage_report}\n")

    input("\n  Press Enter to continue to Act 2...\n")

    _banner("ACT 2 OF 2 — COMPLIANCE AUDIT")
    print("  3 vendor contracts. 8 policy rules.")
    print("  Watch the agent read every clause and flag every violation verbatim.\n")
    run("audit", repo_root, api_key)
    audit_report = reports_dir / f"compliance-audit-{today}.md"
    if audit_report.exists():
        print(f"\n  Report written → {audit_report}\n")

    _banner("DEMO COMPLETE")
    print(f"  Triage report  → {triage_report}")
    print(f"  Audit report   → {audit_report}\n")


def _watch(api_key: str, repo_root: str, poll_interval: int = 5):
    import datetime
    from agent import run

    issues_dir = os.path.join(repo_root, "issues")
    seen = set(glob.glob(os.path.join(issues_dir, "PROD-*.json")))

    print(f"[watch] Monitoring {issues_dir}")
    print(f"[watch] {len(seen)} existing tickets on startup — watching for new ones.")
    print("[watch] Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(poll_interval)
            current = set(glob.glob(os.path.join(issues_dir, "PROD-*.json")))
            new_files = current - seen
            for path in sorted(new_files):
                issue_id = os.path.basename(path).replace(".json", "")
                ts = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
                print(f"[watch] {ts} — new ticket detected: {issue_id}\n")
                today = datetime.date.today().isoformat()
                trigger = (
                    f"A new production incident has just been opened: {issue_id}. "
                    f"Triage it now. Read the full issue body, check all recent deploys "
                    f"within 48 hours prior to its opened_at timestamp, find the matching "
                    f"runbook, and check whether it correlates with any other open incidents. "
                    f"Write your findings to triage-{issue_id}-{today}.md."
                )
                run("triage", repo_root, api_key, trigger_message=trigger)
                print(f"\n[watch] {issue_id} triaged. Resuming watch...\n")
            seen = current
    except KeyboardInterrupt:
        print("\n[watch] Stopped.")


if __name__ == "__main__":
    main()
