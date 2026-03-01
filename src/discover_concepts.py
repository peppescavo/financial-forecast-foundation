"""Discover us-gaap concepts from SEC companyfacts and produce a curated macro list."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from src import config
from src.edgar_client import fetch_company_facts, fetch_cik_universe_with_tickers

FORMS = ("10-K", "10-Q")

# Core fields always included in curated list (even if discovery missed them)
CORE_FINANCIAL_FIELDS = [
    "Revenues",
    "NetIncomeLoss",
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "OperatingIncomeLoss",
    "EBIT",
    "EBITDA",
    "CashAndCashEquivalentsAtCarryingValue",
    "LongTermDebt",
]


def _select_unit_records(field_payload: dict) -> list[dict]:
    """Select preferred units records for a us-gaap field payload (USD preferred)."""
    units = field_payload.get("units", {})
    if "USD" in units:
        return units["USD"]
    for records in units.values():
        return records
    return []


def _concept_has_10k_10q_usd(gaap_facts: dict, concept: str) -> bool:
    """Return True if this concept has at least one 10-K or 10-Q USD fact."""
    field_payload = gaap_facts.get(concept, {})
    records = _select_unit_records(field_payload)
    return any(r.get("form") in FORMS for r in records)


def concepts_reported_for_facts(facts: dict) -> set[str]:
    """Return set of us-gaap concept names that have at least one 10-K/10-Q USD fact."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    return {
        concept
        for concept in gaap_facts
        if _concept_has_10k_10q_usd(gaap_facts, concept)
    }


def run_discovery(
    max_companies: int = 2000,
    output_path: Path | None = None,
) -> Path:
    """Fetch companyfacts for up to max_companies, aggregate concept counts, write coverage file."""
    output_path = output_path or config.RAW_DATA_DIR / "us_gaap_concept_coverage.json"
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    companies = fetch_cik_universe_with_tickers()
    ciks = [cik for cik, _ in companies[:max_companies]]
    total = len(ciks)

    concept_counts: dict[str, int] = defaultdict(int)
    max_workers = getattr(config, "SEC_FETCH_MAX_WORKERS", 6)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cik = {executor.submit(fetch_company_facts, cik): cik for cik in ciks}
        for future in tqdm(
            as_completed(future_to_cik),
            total=len(future_to_cik),
            desc="Fetching companyfacts",
            unit="company",
        ):
            try:
                facts = future.result()
                for concept in concepts_reported_for_facts(facts):
                    concept_counts[concept] += 1
            except Exception:
                pass

    concepts_sorted = sorted(
        concept_counts.items(),
        key=lambda x: -x[1],
    )
    total_ok = total
    out = {
        "total_companies": total_ok,
        "concepts": [
            {
                "concept": c,
                "company_count": n,
                "pct": round(n / total_ok, 4) if total_ok else 0.0,
            }
            for c, n in concepts_sorted
        ],
    }
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    return output_path


def _should_exclude_concept(name: str) -> bool:
    """Exclude concepts that are not statement-level macro accounts."""
    if "PerShare" in name or "EarningsPerShare" in name:
        return True
    return False


def run_curate(
    min_pct: float = 0.02,
    coverage_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """Read coverage file, apply rules, merge core fields, write curated list."""
    coverage_path = (
        coverage_path or config.RAW_DATA_DIR / "us_gaap_concept_coverage.json"
    )
    output_path = output_path or config.RAW_DATA_DIR / "macro_financial_concepts.json"

    core_set = set(CORE_FINANCIAL_FIELDS)
    curated: list[str] = list(CORE_FINANCIAL_FIELDS)

    if not coverage_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(curated, f, indent=2)
        return output_path

    with open(coverage_path) as f:
        data = json.load(f)
    concepts = data.get("concepts", [])

    for item in concepts:
        name = item.get("concept", "")
        pct = item.get("pct", 0.0)
        if name in core_set:
            continue
        if pct < min_pct:
            continue
        if _should_exclude_concept(name):
            continue
        curated.append(name)

    with open(output_path, "w") as f:
        json.dump(curated, f, indent=2)
    return output_path
