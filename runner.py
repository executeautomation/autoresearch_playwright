"""
Fixed test runner for AutonomousTester.

Executes all Playwright tests in tests/test_suite.py, captures structured
results, saves screenshots of failures, and appends a row to results.tsv.

Usage:
    uv run runner.py
    uv run runner.py --description "nav links and login flow"

DO NOT MODIFY THIS FILE.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

RESULTS_TSV = "results.tsv"
SNAPSHOTS_DIR = Path("snapshots")
REPORT_FILE = Path(".report.json")
TEST_TIMEOUT = 30  # seconds per test

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ensure_results_tsv() -> None:
    """Create results.tsv with a header row if it does not already exist."""
    if not os.path.exists(RESULTS_TSV):
        with open(RESULTS_TSV, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(
                [
                    "commit",
                    "passed",
                    "failed",
                    "errors",
                    "duration_s",
                    "coverage_score",
                    "status",
                    "description",
                ]
            )


def get_git_commit() -> str:
    """Return the short (7-char) SHA of the current HEAD commit."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def run_tests() -> tuple[int, float]:
    """
    Run pytest with json-report and screenshot capture.

    Returns (returncode, wall_clock_seconds).
    """
    SNAPSHOTS_DIR.mkdir(exist_ok=True)

    # Remove stale report so parse_report() can detect a missing file.
    REPORT_FILE.unlink(missing_ok=True)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_suite.py",
        "--json-report",
        f"--json-report-file={REPORT_FILE}",
        "--screenshot=only-on-failure",   # playwright screenshot on failure
        f"--output={SNAPSHOTS_DIR}",       # artifact directory
        "-v",
        "--tb=short",
        f"--timeout={TEST_TIMEOUT}",
        "--color=yes",
    ]

    start = time.monotonic()
    result = subprocess.run(cmd)
    duration = time.monotonic() - start

    return result.returncode, duration


def parse_report() -> dict:
    """
    Parse the pytest-json-report JSON file.

    Returns a dict with keys: passed, failed, errors, total.
    Falls back to zeros if the report is missing (e.g. crashed on collection).
    """
    if not REPORT_FILE.exists():
        return {"passed": 0, "failed": 0, "errors": 0, "total": 0}

    with open(REPORT_FILE) as f:
        report = json.load(f)

    summary = report.get("summary", {})
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    errors = summary.get("error", 0)
    total = summary.get("total", passed + failed + errors)

    return {"passed": passed, "failed": failed, "errors": errors, "total": total}


def compute_coverage_score(stats: dict) -> float:
    """Score = passed / total. Returns 0.0 if no tests collected."""
    total = stats["total"]
    if total == 0:
        return 0.0
    return round(stats["passed"] / total, 4)


def determine_status(stats: dict, coverage_score: float) -> str:
    """
    Heuristic status:
      crash   — collection errors and nothing passed
      keep    — coverage_score >= 0.8 (80 %+ passing)
      discard — coverage_score < 0.8
    The agent should override this if the context calls for it.
    """
    if stats["errors"] > 0 and stats["passed"] == 0:
        return "crash"
    if coverage_score >= 0.8:
        return "keep"
    return "discard"


def log_results(
    commit: str,
    stats: dict,
    duration: float,
    coverage_score: float,
    status: str,
    description: str,
) -> None:
    """Append one row to results.tsv."""
    ensure_results_tsv()
    with open(RESULTS_TSV, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                commit,
                stats["passed"],
                stats["failed"],
                stats["errors"],
                f"{duration:.1f}",
                f"{coverage_score:.4f}",
                status,
                description,
            ]
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run all Playwright tests and log results."
    )
    parser.add_argument(
        "--description",
        default="auto",
        help="Short description of this experiment (logged to results.tsv).",
    )
    args = parser.parse_args()

    ensure_results_tsv()
    commit = get_git_commit()

    print(f"AutonomousTester — commit: {commit}")
    print(f"Running tests in tests/test_suite.py ...\n")

    _, duration = run_tests()
    stats = parse_report()
    coverage_score = compute_coverage_score(stats)
    status = determine_status(stats, coverage_score)

    log_results(commit, stats, duration, coverage_score, status, args.description)

    # Print structured summary that the agent can grep
    print()
    print("---")
    print(f"total_tests:    {stats['total']}")
    print(f"passed:         {stats['passed']}")
    print(f"failed:         {stats['failed']}")
    print(f"errors:         {stats['errors']}")
    print(f"duration_s:     {duration:.1f}")
    print(f"coverage_score: {coverage_score:.4f}")
    print(f"status:         {status}")
    print("---")
    print(f"Snapshots saved to: {SNAPSHOTS_DIR}/")
    print(f"Results logged to:  {RESULTS_TSV}")

    if stats["failed"] > 0 or stats["errors"] > 0:
        print(f"\nFailing test screenshots: {SNAPSHOTS_DIR}/*.png")
        print("Read the screenshots and run.log to diagnose failures.")


if __name__ == "__main__":
    main()
