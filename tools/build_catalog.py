#!/usr/bin/env python3
"""Build the deterministic machine-readable treatment catalog."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packs.tools import check as checker


TREATMENTS = ROOT / "packs"
CATALOG = ROOT / "catalog.json"


def build_catalog():
    """Return the validated catalog document and serialized bytes."""
    entries = []
    for path in sorted(TREATMENTS.glob("*.yml")):
        failures, _warnings, _rows = checker.check(path)
        if failures:
            raise ValueError(f"{path}: " + "; ".join(failures))

        raw = path.read_bytes()
        doc = yaml.load(raw.decode("utf-8"), Loader=checker.UniqueKeyLoader)
        entries.append(
            {
                "id": doc["id"],
                "name": doc["name"],
                "category": doc["category"],
                "summary": doc["summary"],
                "fit": doc["fit"],
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    catalog = {
        "format": "design-treatment-catalog/v1",
        "count": len(entries),
        "treatments": entries,
    }
    serialized = (json.dumps(catalog, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    return catalog, serialized


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when catalog.json is missing or differs from generated output",
    )
    args = parser.parse_args(argv)

    catalog, serialized = build_catalog()
    if args.check:
        current = CATALOG.read_bytes() if CATALOG.is_file() else b""
        if current != serialized:
            print("catalog.json is stale; run: python3 tools/build_catalog.py")
            return 1
        print(f"catalog.json is current ({catalog['count']} treatments)")
        return 0

    CATALOG.write_bytes(serialized)
    print(f"Wrote {CATALOG.relative_to(ROOT)} ({catalog['count']} treatments)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
