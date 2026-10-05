from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "scripts" / "content" / "safe_power_batch.py",
    ROOT / "scripts" / "content" / "run_power_grade.py",
]

REPLACEMENTS = [
    (
        '        m = re.search(rf"^{re.escape(label)}:\\s*(\\d+)\\s*$", out, re.MULTILINE)\n'
        '        if m:\n'
        '            result[key] = int(m.group(1))',
        '        matches = re.findall(rf"^{re.escape(label)}:\\s*(\\d+)\\s*$", out, re.MULTILINE)\n'
        '        if matches:\n'
        '            result[key] = int(matches[-1])',
    ),
    (
        '        m = re.search(rf"^{re.escape(label)}:\\s*(\\d+)\\s*$", output, re.MULTILINE)\n'
        '        if m:\n'
        '            result[key] = int(m.group(1))',
        '        matches = re.findall(rf"^{re.escape(label)}:\\s*(\\d+)\\s*$", output, re.MULTILINE)\n'
        '        if matches:\n'
        '            result[key] = int(matches[-1])',
    ),
]

def main():
    changed = 0
    for path in TARGETS:
        if not path.exists():
            print(f"[ERROR] Missing file: {path}")
            return 2

        original = path.read_text(encoding="utf-8")
        src = original

        for old, new in REPLACEMENTS:
            src = src.replace(old, new)

        if src == original:
            print(f"[INFO] No matching parser block found in {path}")
            continue

        backup = path.with_suffix(path.suffix + ".v142.bak")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")

        path.write_text(src, encoding="utf-8")
        print(f"[OK] Patched: {path}")
        changed += 1

    if changed == 0:
        print("[ERROR] No files were patched.")
        return 3

    print("[OK] Status parser now uses the LAST status block in command output.")
    print("[NEXT] Re-run: python scripts\\content\\run_power_grade.py --grade 10 --limit 5")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
