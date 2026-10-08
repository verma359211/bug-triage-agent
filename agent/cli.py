import argparse
import json
import sys
from pathlib import Path

from agent.graph import run_agent


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Investigate a software defect report")
    parser.add_argument("--repo", required=True, help="Public GitHub repository URL")
    parser.add_argument("--report", required=True, help="Bug report text")
    parser.add_argument("--output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--quiet", action="store_true", help=argparse.SUPPRESS)
    arguments = parser.parse_args()

    result = run_agent(arguments.repo, arguments.report, save=arguments.output is None)
    report = {key: value for key, value in result["report"].items() if key != "markdown"}
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not arguments.quiet:
        print()
        print(result["report"]["markdown"])
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
