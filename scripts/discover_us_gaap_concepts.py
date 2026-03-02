"""
Discover us-gaap concepts from SEC companyfacts and produce a curated macro list.

Usage:
  python scripts/discover_us_gaap_concepts.py [--max-companies N] [--output PATH]
  python scripts/discover_us_gaap_concepts.py --curate [--min-pct P] [--coverage PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root so src is importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.discover_concepts import run_curate, run_discovery  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover us-gaap concepts from SEC companyfacts and/or produce curated macro list."
    )
    parser.add_argument(
        "--curate",
        action="store_true",
        help="Run curation only (read coverage, write macro_financial_concepts.json).",
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=2000,
        help="Max companies to fetch for discovery (default 2000).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (discovery: coverage JSON; curate: curated list JSON).",
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        default=None,
        help="Path to coverage JSON (for --curate). Default: data/raw/us_gaap_concept_coverage.json",
    )
    parser.add_argument(
        "--min-pct",
        type=float,
        default=0.02,
        help="Min fraction of companies for curated concept (default 0.02).",
    )
    args = parser.parse_args()

    if args.curate:
        run_curate(
            min_pct=args.min_pct,
            coverage_path=args.coverage,
            output_path=args.output,
        )
        return 0
    run_discovery(
        max_companies=args.max_companies,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
