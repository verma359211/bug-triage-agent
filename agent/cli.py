import argparse
import json
import sys

from agent.graph import run_agent


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Investigate a software defect report")
    parser.add_argument("--repo", required=True, help="Public GitHub repository URL")
    parser.add_argument("--report", required=True, help="Bug report text")
    arguments = parser.parse_args()

    result = run_agent(arguments.repo, arguments.report)
    print()
    print(result["report"]["markdown"])
    print(json.dumps({key: value for key, value in result["report"].items() if key != "markdown"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
