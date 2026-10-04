from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def fetch(path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(BASE + path, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {"detail": str(exc)}
        return exc.code, payload


def main() -> int:
    checks = [
        ("liveness", "/health/live", 200),
        ("database health", "/health", 200),
        ("readiness", "/health/ready", 200),
    ]
    ok = True
    for label, path, expected in checks:
        try:
            status, payload = fetch(path)
            passed = status == expected
            ok &= passed
            print(f"[{'PASS' if passed else 'FAIL'}] {label}: HTTP {status} {payload}")
        except Exception as exc:
            ok = False
            print(f"[FAIL] {label}: {exc}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
