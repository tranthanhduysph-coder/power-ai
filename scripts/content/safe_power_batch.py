from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_POWER = REPO_ROOT / "scripts" / "content" / "build_power.py"


def _utf8_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _safe_write(value: str) -> None:
    # Avoid Windows cp1252 crashes even if a replacement character appears.
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sys.stdout.write(value)
    except UnicodeEncodeError:
        sys.stdout.write(value.encode(encoding, errors="replace").decode(encoding, errors="replace"))
    sys.stdout.flush()


def run_cmd(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(BUILD_POWER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=_utf8_env(),
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    _safe_write(output if output.endswith("\n") else output + "\n")
    return proc.returncode, output


def fail_reason(output: str) -> list[str]:
    reasons: list[str] = []
    if "[ERROR]" in output:
        reasons.append("generation/validation output contains [ERROR]")
    if "[FAIL]" in output:
        reasons.append("QA output contains [FAIL]")
    if "Traceback (most recent call last)" in output:
        reasons.append("Python traceback detected")
    if "NameError:" in output:
        reasons.append("NameError detected")
    if "StatementError:" in output or "ProgrammingError:" in output:
        reasons.append("database activation error detected")
    return reasons


def parse_status(output: str) -> dict[str, int]:
    keys = {
        "Eligible ingested units": "eligible",
        "POWER-ready": "ready",
        "QA-passed awaiting activation": "qa_wait",
        "Validated awaiting QA": "validated_wait",
        "Draft needs regeneration/fix": "draft_fix",
        "Not started": "not_started",
    }
    result: dict[str, int] = {}
    for label, key in keys.items():
        matches = re.findall(rf"^{re.escape(label)}:\s*(\d+)\s*$", output, re.MULTILINE)
        if matches:
            result[key] = int(matches[-1])
    return result


def status(grade: int) -> dict[str, int]:
    print(f"\n=== STATUS GRADE {grade} ===")
    rc, out = run_cmd(["status", "--grade", str(grade)])
    if rc != 0:
        raise SystemExit(rc)
    return parse_status(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Conservative POWER batch runner: generate -> QA -> activate only when the whole batch is clean."
    )
    ap.add_argument("--grade", type=int, choices=[10, 11, 12], required=True)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--status-only", action="store_true")
    args = ap.parse_args()

    before = status(args.grade)
    if args.status_only:
        return 0

    eligible = before.get("eligible")
    ready = before.get("ready")

    if eligible is not None and eligible == 0:
        print("\n[STOP] No ingested units are eligible. Ingest/reconcile textbook content first.")
        return 20

    if eligible is not None and ready is not None and ready >= eligible:
        print(f"\n[DONE] Grade {args.grade} is already {ready}/{eligible} POWER-ready.")
        return 0

    print(f"\n=== GENERATE GRADE {args.grade} - LIMIT {args.limit} ===")
    rc, gen = run_cmd(["generate", "--grade", str(args.grade), "--limit", str(args.limit)])
    if rc != 0:
        print("\n[STOP] Generate returned a non-zero exit code. Nothing will be activated.")
        return rc

    reasons = fail_reason(gen)
    if reasons:
        print("\n[STOP] Generate produced a problem. Nothing will be activated.")
        for reason in reasons:
            print(" -", reason)
        return 21

    print(f"\n=== QA GRADE {args.grade} - LIMIT {args.limit} ===")
    rc, qa = run_cmd(["qa", "--grade", str(args.grade), "--limit", str(args.limit)])
    if rc != 0:
        print("\n[STOP] QA returned a non-zero exit code. Nothing will be activated.")
        return rc

    reasons = fail_reason(qa)
    if reasons:
        print("\n[STOP] QA is not completely clean. Nothing will be activated.")
        for reason in reasons:
            print(" -", reason)
        return 22

    if "[WARN]" in qa:
        print("\n[STOP] QA contains [WARN]. Nothing will be activated.")
        return 23

    if "[PASS]" not in qa:
        print("\n[STOP] QA produced no [PASS] draft. Nothing will be activated.")
        return 24

    print(f"\n=== ACTIVATE CLEAN BATCH - GRADE {args.grade} ===")
    rc, act = run_cmd([
        "activate-batch",
        "--grade", str(args.grade),
        "--limit", str(args.limit),
        "--confirm", "ACTIVATE-QA-PASSED",
    ])
    if rc != 0:
        print("\n[STOP] Activation returned a non-zero exit code.")
        return rc

    reasons = fail_reason(act)
    if reasons:
        print("\n[STOP] Activation output contains an error.")
        for reason in reasons:
            print(" -", reason)
        return 25

    after = status(args.grade)

    b_ready = before.get("ready")
    a_ready = after.get("ready")
    if b_ready is not None and a_ready is not None:
        print(f"\n[OK] POWER-ready: {b_ready} -> {a_ready}")

    if (
        after.get("eligible") is not None
        and after.get("ready") == after.get("eligible")
        and after.get("qa_wait", 0) == 0
        and after.get("validated_wait", 0) == 0
        and after.get("draft_fix", 0) == 0
        and after.get("not_started", 0) == 0
    ):
        print(f"[DONE] Grade {args.grade} is fully POWER-ready with no intermediate drafts.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
