from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(name: str, command: list[str], cwd: Path | None = None) -> bool:
    print("\n" + "=" * 72)
    print(f"Running: {name}")
    print("=" * 72)
    print("Command:", " ".join(command))

    result = subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
    )

    if result.returncode == 0:
        print(f"✅ PASS: {name}")
        return True

    print(f"❌ FAIL: {name}")
    return False


def main() -> int:
    checks = [
        (
            "Backend test suite",
            [sys.executable, "-m", "pytest", "backend/app/tests", "-q"],
            ROOT,
        ),
        (
            "ML evaluation suite",
            [sys.executable, "scripts/run_ml_evaluation.py"],
            ROOT,
        ),
        (
            "Risk calibrator evaluation",
            [sys.executable, "scripts/evaluate_risk_calibrator.py"],
            ROOT,
        ),
        (
            "Live news simulation",
            [sys.executable, "scripts/check_live_news_simulation.py"],
            ROOT,
        ),
        (
            "Timeline anomaly detection",
            [sys.executable, "scripts/check_timeline_anomalies.py"],
            ROOT,
        ),
        (
            "HTML report generation",
            [sys.executable, "scripts/generate_report.py"],
            ROOT,
        ),
        (
            "PDF report generation",
            [sys.executable, "scripts/generate_pdf_report.py"],
            ROOT,
        ),
        (
            "Frontend production build",
            ["npm", "run", "build"],
            ROOT / "frontend",
        ),
    ]

    results = []

    for name, command, cwd in checks:
        results.append(run_command(name, command, cwd))

    passed = sum(1 for item in results if item)
    total = len(results)

    print("\n" + "=" * 72)
    print("RiskLens Alpha Final Project Check")
    print("=" * 72)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ FINAL STATUS: PROJECT VALIDATION PASSED")
        return 0

    print("❌ FINAL STATUS: SOME CHECKS FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
