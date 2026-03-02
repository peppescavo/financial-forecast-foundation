"""Tests for us-gaap concept discovery and curation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.discover_concepts import (
    CORE_FINANCIAL_FIELDS,
    concepts_reported_for_facts,
    run_curate,
    run_discovery,
)


def test_concepts_reported_for_facts_empty() -> None:
    """Empty facts returns empty set."""
    assert concepts_reported_for_facts({}) == set()
    assert concepts_reported_for_facts({"facts": {}}) == set()
    assert concepts_reported_for_facts({"facts": {"us-gaap": {}}}) == set()


def test_concepts_reported_for_facts_mock() -> None:
    """Mock companyfacts: only concepts with 10-K/10-Q USD facts are returned."""
    facts = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [{"form": "10-K", "end": "2024-12-31", "val": 100}]
                    },
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [{"form": "10-Q", "end": "2024-09-30", "val": 10}]
                    },
                },
                "SomeAbstract": {"units": {"USD": []}},
                "EarningsPerShareBasic": {
                    "units": {
                        "USD": [{"form": "10-K", "end": "2024-12-31", "val": 1.0}]
                    },
                },
                "NoRelevantForm": {
                    "units": {"USD": [{"form": "8-K", "end": "2024-01-01", "val": 1}]},
                },
            },
        },
    }
    got = concepts_reported_for_facts(facts)
    assert "Revenues" in got
    assert "NetIncomeLoss" in got
    assert "EarningsPerShareBasic" in got
    assert "SomeAbstract" not in got
    assert "NoRelevantForm" not in got


def test_run_curate_no_coverage_file() -> None:
    """Curation with missing coverage file writes core list only."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "macro.json"
        cov = Path(tmp) / "nonexistent_coverage.json"
        run_curate(coverage_path=cov, output_path=out, min_pct=0.02)
        assert out.exists()
        with open(out) as f:
            curated = json.load(f)
        assert curated == CORE_FINANCIAL_FIELDS


def test_run_curate_with_coverage() -> None:
    """Curation includes concepts above min_pct and excludes PerShare."""
    with tempfile.TemporaryDirectory() as tmp:
        cov_path = Path(tmp) / "coverage.json"
        out_path = Path(tmp) / "macro.json"
        coverage = {
            "total_companies": 100,
            "concepts": [
                {"concept": "Revenues", "company_count": 99, "pct": 0.99},
                {"concept": "OtherConcept", "company_count": 50, "pct": 0.50},
                {"concept": "RareConcept", "company_count": 1, "pct": 0.01},
                {"concept": "EarningsPerShareBasic", "company_count": 80, "pct": 0.80},
                {"concept": "WideConcept", "company_count": 10, "pct": 0.10},
            ],
        }
        with open(cov_path, "w") as f:
            json.dump(coverage, f, indent=2)

        run_curate(
            min_pct=0.05,
            coverage_path=cov_path,
            output_path=out_path,
        )
        with open(out_path) as f:
            curated = json.load(f)

    # Core always present
    for c in CORE_FINANCIAL_FIELDS:
        assert c in curated
    # Above min_pct (0.05): OtherConcept 0.5, WideConcept 0.10
    assert "OtherConcept" in curated
    assert "WideConcept" in curated
    # Below min_pct
    assert "RareConcept" not in curated
    # Excluded by name
    assert "EarningsPerShareBasic" not in curated


@pytest.mark.integration
def test_run_discovery_small_integration() -> None:
    """Discovery with 2 companies produces valid coverage JSON (hits network)."""
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "coverage.json"
        run_discovery(max_companies=2, output_path=out_path)
        assert out_path.exists()
        with open(out_path) as f:
            data = json.load(f)
        assert data["total_companies"] == 2
        assert "concepts" in data
        assert isinstance(data["concepts"], list)
        for item in data["concepts"]:
            assert "concept" in item
            assert "company_count" in item
            assert "pct" in item


def test_curated_list_contains_core_and_extra() -> None:
    """Curate output file contains all core fields and any concepts passing filters."""
    with tempfile.TemporaryDirectory() as tmp:
        cov_path = Path(tmp) / "coverage.json"
        out_path = Path(tmp) / "macro.json"
        with open(cov_path, "w") as f:
            json.dump(
                {
                    "total_companies": 100,
                    "concepts": [
                        {"concept": "Revenues", "company_count": 100, "pct": 1.0},
                        {"concept": "ExtraConcept", "company_count": 50, "pct": 0.5},
                    ],
                },
                f,
            )
        run_curate(
            min_pct=0.02,
            coverage_path=cov_path,
            output_path=out_path,
        )
        with open(out_path) as f:
            curated = json.load(f)
        for c in CORE_FINANCIAL_FIELDS:
            assert c in curated
        assert "ExtraConcept" in curated
