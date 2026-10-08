import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.graph import run_agent
from agent.llm import load_dotenv


def cause_matches(report: dict, expected_keywords: list[str]) -> bool:
    """Return true when at least 75% of the expected cause terms are present."""
    if not expected_keywords:
        return True
    explanation = f"{report.get('cause', '')} {report.get('reasoning', '')}".casefold()
    matches = sum(keyword.casefold() in explanation for keyword in expected_keywords)
    return matches / len(expected_keywords) >= 0.75


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(ROOT / ".env")
    repo_url = os.environ["TARGET_REPO"]
    cases = json.loads((Path(__file__).parent / "bugs.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description="Run bug-triage evaluation cases")
    parser.add_argument("--case", action="append", dest="case_ids")
    arguments = parser.parse_args()
    if arguments.case_ids:
        selected = set(arguments.case_ids)
        cases = [case for case in cases if case["id"] in selected]
        unknown = selected - {case["id"] for case in cases}
        if unknown:
            parser.error(f"unknown case: {', '.join(sorted(unknown))}")
    rows = []

    for case in cases:
        print(f"\n=== {case['id']} ===")
        try:
            state = run_agent(repo_url, case["report"])
            actual_file = state["report"]["file"]
            file_match = actual_file == case["expected_file"]
            cause_match = cause_matches(
                state["report"], case["expected_cause_keywords"]
            )
            expected_status = (
                "reproduced" if case["repro_expected"] else "hypothesis_only_frontend"
            )
            status_match = state["report"]["status"] == expected_status
            rows.append(
                {
                    "id": case["id"],
                    "expected": case["expected_file"],
                    "actual": actual_file,
                    "file_match": file_match,
                    "cause_match": cause_match,
                    "status_match": status_match,
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
                    "file_match": False,
                    "cause_match": False,
                    "status_match": False,
                    "confidence": "-",
                    "status": "error",
                    "seconds": 0.0,
                }
            )
            print(f"evaluation error: {error}")

    print()
    print(
        f"{'case':<20} {'file':<7} {'cause':<7} {'status':<7} "
        f"{'confidence':<11} {'result':<27} {'seconds':>8}  actual"
    )
    print("-" * 113)
    for row in rows:
        print(
            f"{row['id']:<20} {str(row['file_match']):<7} "
            f"{str(row['cause_match']):<7} {str(row['status_match']):<7} "
            f"{row['confidence']:<11} "
            f"{row['status']:<27} {row['seconds']:>8.2f}  {row['actual']}"
        )
    file_matches = sum(row["file_match"] for row in rows)
    cause_matches_count = sum(row["cause_match"] for row in rows)
    status_matches = sum(row["status_match"] for row in rows)
    print(f"\nFile matches: {file_matches}/{len(rows)}")
    print(f"Cause matches: {cause_matches_count}/{len(rows)}")
    print(f"Status matches: {status_matches}/{len(rows)}")
    required_file_matches = 3 if len(rows) >= 4 else len(rows)
    return (
        0
        if file_matches >= required_file_matches
        and cause_matches_count == len(rows)
        and status_matches == len(rows)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
