"""
Synthetic ticket + deploy generator for the always-on-agent demo loop.

Drops a new PROD-XXXX.json into issues/ and appends a matching deploy
to deploys/recent.json so the triage agent finds a real correlation.

Usage (from agent/):
    python generator.py           # generate one ticket and exit
    python generator.py --loop    # generate a new ticket every 60s
"""

import datetime
import glob
import json
import os
import random
import sys
import time

SCENARIOS = [
    {
        "title": "NullPointerException in PaymentService — EU tenants affected",
        "labels": ["customer-impact", "payment"],
        "body": (
            "Multiple EU enterprise tenants reporting checkout failures starting ~15 minutes ago. "
            "Error: NullPointerException in PaymentService at checkout confirmation step. "
            "Affects tenants enrolled in the guest checkout beta. US tenants appear unaffected. "
            "Estimated 800 impacted users across three accounts. Escalated by EMEA CSM team."
        ),
        "deploy": {
            "service": "payment-service",
            "version": "v4.8.3",
            "summary": "Extend guest checkout support to EU region",
            "files_changed": ["PaymentService.java", "config/regions.yaml"],
            "rollback_available": True,
            "last_known_good": "v4.8.2",
            "deployed_by": "ci-bot@bts-synthetic.example",
        },
    },
    {
        "title": "Auth service pod restart loop — login success rate dropping",
        "labels": ["service-health"],
        "body": (
            "auth-service pods entering OOMKill restart loop in us-east-1. Memory climbed from "
            "512MB baseline to 1.8GB over 20 minutes before restart. Login success rate dropped "
            "from 99.7% to 87.2%. Each restart causes ~40s of failed logins. "
            "Pattern is worsening — restart frequency increasing."
        ),
        "deploy": {
            "service": "auth-service",
            "version": "v6.0.1",
            "summary": "Increase Redis session cache TTL from 3600s to 86400s",
            "files_changed": ["config/prod.yaml"],
            "rollback_available": True,
            "last_known_good": "v6.0.0",
            "deployed_by": "maya.singh@bts-synthetic.example",
        },
    },
    {
        "title": "Stripe webhook delivery failures — payment confirmations delayed",
        "labels": ["payment", "third-party"],
        "body": (
            "Stripe webhook endpoint returning 504s for payment confirmation events. "
            "Payments processing correctly but confirmation webhooks timing out — "
            "order fulfillment is delayed. Queue depth at ~3,200 undelivered events and growing. "
            "Stripe confirmed the issue is on our endpoint. Customers reporting missing order emails."
        ),
        "deploy": {
            "service": "webhook-service",
            "version": "v2.3.0",
            "summary": "Add HMAC signature validation for all inbound Stripe webhooks",
            "files_changed": ["WebhookController.java", "SignatureValidator.java"],
            "rollback_available": True,
            "last_known_good": "v2.2.1",
            "deployed_by": "tom.bryce@bts-synthetic.example",
        },
    },
    {
        "title": "Background job queue depth spiking — email notifications 2hr delayed",
        "labels": ["performance"],
        "body": (
            "Worker queue depth climbed from steady-state ~200 to 47,000 jobs over 30 minutes. "
            "Email notifications, PDF exports, and data jobs all delayed. "
            "Consumer pods are running but throughput dropped from ~400 jobs/min to ~12 jobs/min. "
            "No consumer error logs visible — processing is slow, not failing. SLA breach imminent."
        ),
        "deploy": {
            "service": "worker-service",
            "version": "v3.1.0",
            "summary": "Integrate ML-based job prioritisation model",
            "files_changed": ["JobPrioritiser.java", "WorkerPool.java", "config/worker.yaml"],
            "rollback_available": True,
            "last_known_good": "v3.0.4",
            "deployed_by": "yuki.tanaka@bts-synthetic.example",
        },
    },
    {
        "title": "CDN cache invalidation cascade — global API latency spike",
        "labels": ["performance", "infrastructure"],
        "body": (
            "All CDN edge nodes simultaneously invalidating cache after a config push. "
            "Origin servers absorbing 100% of traffic while caches warm. "
            "Global p99 latency jumped from 180ms to 4.2s. Auto-scaling is firing. "
            "Cache warm-up estimated 15-20 minutes. All static assets and API responses affected."
        ),
        "deploy": {
            "service": "cdn-config-service",
            "version": "v1.0.5",
            "summary": "Reduce API response cache TTL from 300s to 60s for real-time accuracy",
            "files_changed": ["cdn/cache-rules.yaml"],
            "rollback_available": True,
            "last_known_good": "v1.0.4",
            "deployed_by": "ci-bot@bts-synthetic.example",
        },
    },
]


def next_issue_id(repo_root: str) -> str:
    paths = glob.glob(os.path.join(repo_root, "issues/PROD-*.json"))
    if not paths:
        return "PROD-4522"
    ids = [
        int(os.path.basename(p).replace("PROD-", "").replace(".json", ""))
        for p in paths
    ]
    return f"PROD-{max(ids) + 1}"


def generate(repo_root: str, scenario: dict = None) -> str:
    if scenario is None:
        scenario = random.choice(SCENARIOS)

    issue_id = next_issue_id(repo_root)
    now = datetime.datetime.now(datetime.UTC)
    opened_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Deploy happened ~20 minutes before the ticket opened
    deploy_time = (now - datetime.timedelta(minutes=random.randint(15, 25)))
    deployed_at = deploy_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Write the issue
    issue = {
        "id": issue_id,
        "title": scenario["title"],
        "status": "open",
        "severity": None,
        "labels": scenario["labels"],
        "assignee": None,
        "opened_at": opened_at,
        "reporter": "monitoring@bts-synthetic.example",
        "body": scenario["body"],
        "comments": [],
    }
    issue_path = os.path.join(repo_root, f"issues/{issue_id}.json")
    with open(issue_path, "w") as f:
        json.dump(issue, f, indent=2)

    # Append the matching deploy to deploys/recent.json
    deploys_path = os.path.join(repo_root, "deploys/recent.json")
    with open(deploys_path) as f:
        deploy_data = json.load(f)

    new_deploy = {
        "service": scenario["deploy"]["service"],
        "version": scenario["deploy"]["version"],
        "deployed_at": deployed_at,
        "deployed_by": scenario["deploy"]["deployed_by"],
        "commit": f"{random.randint(0x1000000, 0xfffffff):07x}",
        "summary": scenario["deploy"]["summary"],
        "files_changed": scenario["deploy"]["files_changed"],
        "rollback_available": scenario["deploy"]["rollback_available"],
        "last_known_good": scenario["deploy"]["last_known_good"],
    }
    deploy_data["deploys"].insert(0, new_deploy)

    with open(deploys_path, "w") as f:
        json.dump(deploy_data, f, indent=2)

    print(
        f"[generator] {issue_id} — {scenario['title'][:60]}...\n"
        f"            deploy: {new_deploy['service']} {new_deploy['version']} "
        f"at {deployed_at} ({(now - deploy_time).seconds // 60}min before ticket)\n"
    )
    return issue_id


def loop(repo_root: str, interval: int = 60):
    print(f"[generator] Running — new ticket every {interval}s. Ctrl+C to stop.\n")
    scenarios = list(SCENARIOS)
    random.shuffle(scenarios)
    idx = 0
    while True:
        scenario = scenarios[idx % len(scenarios)]
        idx += 1
        generate(repo_root, scenario)
        print(f"[generator] Next ticket in {interval}s...\n")
        time.sleep(interval)


if __name__ == "__main__":
    import pathlib
    repo_root = str(pathlib.Path(__file__).parent.parent.resolve())
    if "--loop" in sys.argv:
        interval = 60
        for i, arg in enumerate(sys.argv):
            if arg == "--interval" and i + 1 < len(sys.argv):
                interval = int(sys.argv[i + 1])
        loop(repo_root, interval)
    else:
        generate(repo_root)
