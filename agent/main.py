#!/usr/bin/env python3
import os
import pathlib
import sys

from dotenv import load_dotenv


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("triage", "audit"):
        print("Usage: python main.py [triage|audit]")
        sys.exit(1)

    mode = sys.argv[1]

    # Load API key from .env at repo root
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.environ.get("api_key")
    if not api_key:
        print(f"Error: 'api_key' not found in {env_path}")
        sys.exit(1)

    repo_root = str(pathlib.Path(__file__).parent.parent.resolve())

    # Ensure reports directory exists
    reports_dir = pathlib.Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    from agent import run
    run(mode, repo_root, api_key)


if __name__ == "__main__":
    main()
