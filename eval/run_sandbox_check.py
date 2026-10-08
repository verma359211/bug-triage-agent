import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.tools.sandbox import get_default_branch_sha, run_repro


SAMPLES = (
    ("coupon", "repro_samples/coupon.test.js", "reproduced"),
    ("passing", "repro_samples/passing.test.js", "not_reproduced"),
    ("syntax-error", "repro_samples/syntax-error.test.js", "repro_broken"),
)


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError(f"Create {env_path} from .env.example before running this check")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def main() -> int:
    load_dotenv()
    token = os.environ["GITHUB_TOKEN"]
    repo_url = os.environ["TARGET_REPO"]
    commit_sha = get_default_branch_sha(repo_url, token)
    rows = []

    for sample_name, relative_path, expected in SAMPLES:
        source = (Path(__file__).parent / relative_path).read_text(encoding="utf-8")
        for attempt in range(1, 4):
            result = run_repro(
                source,
                commit_sha,
                repo_url=repo_url,
                token=token,
            )
            actual = result["classification"]
            rows.append((sample_name, attempt, expected, actual, result["seconds"]))
            print(
                f"{sample_name:<12} {attempt:^7} {expected:<16} "
                f"{actual:<16} {result['seconds']:>8.2f}"
            )

    print()
    print(f"{'sample':<12} {'attempt':^7} {'expected':<16} {'actual':<16} {'seconds':>8}")
    print("-" * 65)
    for sample_name, attempt, expected, actual, seconds in rows:
        print(f"{sample_name:<12} {attempt:^7} {expected:<16} {actual:<16} {seconds:>8.2f}")

    matched = sum(expected == actual for _, _, expected, actual, _ in rows)
    print(f"\nMatched: {matched}/{len(rows)}")
    return 0 if matched == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
