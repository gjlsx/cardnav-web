"""Safe local diagnostic for a selected source; never sends HTTP requests."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collection_lib.fixtures import fixtures_for_source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    rows = fixtures_for_source(args.source)
    print(f"source={args.source}")
    print(f"fixture_rows={len(rows)}")
    print("network_requests=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
