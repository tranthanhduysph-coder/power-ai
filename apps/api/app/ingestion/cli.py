from __future__ import annotations

import argparse
import json

from app.db.session import SessionLocal
from app.ingestion.service import ingest_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a POWER AI knowledge source manifest")
    parser.add_argument("--manifest", required=True, help="Path to JSON ingestion manifest")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = ingest_manifest(db, args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
