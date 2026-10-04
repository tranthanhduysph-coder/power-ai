from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
WEB_DIR = ROOT / "apps" / "web"


def run(label: str, command: list[str], cwd: Path) -> bool:
    print(f"\n=== {label} ===")
    print(" ".join(command))
    proc = subprocess.run(command, cwd=cwd, check=False)
    if proc.returncode != 0:
        print(f"FAIL: {label}")
        return False
    print(f"PASS: {label}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="POWER AI v1.0 local release checks")
    parser.add_argument("--skip-db", action="store_true", help="Skip database verification")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip checks against running API")
    args = parser.parse_args()

    ok = True
    ok &= run("Python compile", [sys.executable, "-m", "compileall", "app"], API_DIR)
    ok &= run("Backend tests", [sys.executable, "-m", "pytest", "-q"], API_DIR)
    ok &= run("Frontend production build", ["cmd", "/c", "npm", "run", "build"], WEB_DIR)

    if not args.skip_db:
        ok &= run("Database release verification", [sys.executable, str(ROOT / "scripts" / "release" / "verify_local_release.py")], ROOT)
    if not args.skip_smoke:
        ok &= run("Running service smoke test", [sys.executable, str(ROOT / "scripts" / "release" / "smoke_local.py")], ROOT)

    print("\n==============================")
    print("POWER AI v1.0 LOCAL:", "READY" if ok else "NOT READY")
    print("==============================")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
