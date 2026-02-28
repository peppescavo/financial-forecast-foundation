"""Unit tests for reference-date cutoff behavior."""

from __future__ import annotations

import math

from src.xbrl_parser import extract_latest_annual_value_and_end_date


def test_extract_latest_annual_value_and_end_date_reference_date_cutoff() -> None:
    facts = {
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "form": "10-K",
                                "end": "2021-12-31",
                                "filed": "2022-02-15",
                                "val": 100,
                            },
                            {
                                "form": "10-K",
                                "end": "2022-12-31",
                                "filed": "2023-02-20",
                                "val": 200,
                            },
                            {
                                "form": "10-K",
                                "end": "2023-12-31",
                                "filed": "2024-02-25",
                                "val": 300,
                            },
                            {
                                "form": "10-Q",
                                "end": "2024-03-31",
                                "filed": "2024-05-01",
                                "val": 999,
                            },
                        ]
                    }
                }
            }
        }
    }

    value, end = extract_latest_annual_value_and_end_date(facts, "Assets")
    assert value == 300.0
    assert end == "2023-12-31"

    value, end = extract_latest_annual_value_and_end_date(
        facts, "Assets", reference_date="2022-12-31"
    )
    assert value == 200.0
    assert end == "2022-12-31"

    value, end = extract_latest_annual_value_and_end_date(
        facts, "Assets", reference_date="2022-01-01"
    )
    assert value == 100.0
    assert end == "2021-12-31"

    value, end = extract_latest_annual_value_and_end_date(
        facts, "Assets", reference_date="2020-01-01"
    )
    assert math.isnan(value)
    assert end is None
