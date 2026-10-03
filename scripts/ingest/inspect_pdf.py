from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import pymupdf  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect whether a PDF has a usable text layer")
    parser.add_argument("pdf", help="PDF path relative to repository root or absolute path")
    parser.add_argument("--sample-pages", default="1,5,10", help="Comma-separated 1-based PDF pages")
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.is_absolute():
        pdf = ROOT / pdf
    if not pdf.exists():
        raise SystemExit(f"Not found: {pdf}")

    requested = [int(x.strip()) for x in args.sample_pages.split(",") if x.strip()]
    with pymupdf.open(pdf) as doc:
        print(f"PDF: {pdf}")
        print(f"TOTAL_PAGES={len(doc)}")
        for number in requested:
            if not 1 <= number <= len(doc):
                print(f"PAGE {number}: OUT_OF_RANGE")
                continue
            text = (doc[number - 1].get_text("text") or "").strip()
            print(f"PAGE {number}: NATIVE_TEXT_CHARS={len(text)}")
            if text:
                print(" ".join(text[:240].split()))


if __name__ == "__main__":
    main()
