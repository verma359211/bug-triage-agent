import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.graph import run_agent
from agent.llm import load_dotenv


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(ROOT / ".env")
    repo_url = os.environ["TARGET_REPO"]
    cases = json.loads((Path(__file__).parent / "bugs.json").read_text(encoding="utf-8"))
    rows = []

    for case in cases:
        print(f"\n=== {case['id']} ===")
        try:
            state = run_agent(repo_url, case["report"])
            actual_file = state["report"]["file"]
            matched = actual_file == case["expected_file"]
            rows.append(
                {
                    "id": case["id"],
                    "expected": case["expected_file"],
                    "actual": actual_file,
                    "match": matched,
                    "confidence": state["report"]["confidence"],
                    "status": state["report"]["status"],
                    "seconds": state["report"]["total_seconds"],
                }
            )
        except Exception as error:
            rows.append(
                {
                    "id": case["id"],
                    "expected": case["expected_file"],
                    "actual": f"ERROR: {type(error).__name__}",
                    "match": False,
                    "confidence": "-",
                    "status": "error",
                    "seconds": 0.0,
                }
            )
            print(f"evaluation error: {error}")

    print()
    print(f"{'case':<20} {'match':<7} {'confidence':<11} {'status':<27} {'seconds':>8}  actual")
    print("-" * 105)
    for row in rows:
        print(
            f"{row['id']:<20} {str(row['match']):<7} {row['confidence']:<11} "
            f"{row['status']:<27} {row['seconds']:>8.2f}  {row['actual']}"
        )
    matched = sum(row["match"] for row in rows)
    print(f"\nFile matches: {matched}/{len(rows)}")
    return 0 if matched >= 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
