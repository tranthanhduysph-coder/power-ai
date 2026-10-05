from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "content" / "build_kntt.py"


def main() -> int:
    failures = 0
    for grade in (10, 11, 12):
        print(f"\n=== Biology {grade} ===")
        result = subprocess.run([sys.executable, str(SCRIPT), "verify", "--grade", str(grade)], cwd=ROOT, check=False)
        if result.returncode != 0:
            failures += 1
    print("\nPOWER AI KNTT content build:", "READY" if failures == 0 else f"NOT READY ({failures} grade(s) incomplete)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
