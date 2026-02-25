"""Parsers for extracting normalized financial fields from SEC companyfacts."""

from __future__ import annotations

import math

from src.utils import parse_date


def _select_unit_records(field_payload: dict) -> list[dict]:
    """Select preferred units records for a us-gaap field payload."""
    units = field_payload.get("units", {})
    if "USD" in units:
        return units["USD"]
    for records in units.values():
        return records
    return []


def _extract_latest_annual_record(facts: dict, field: str) -> dict | None:
    """Extract the latest annual 10-K record for a us-gaap field."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    field_payload = gaap_facts.get(field, {})
    records = _select_unit_records(field_payload)

    annual_records = [record for record in records if record.get("form") == "10-K"]
    if not annual_records:
        return None

    return max(
        annual_records,
        key=lambda record: (
            parse_date(record.get("end")),
            parse_date(record.get("filed")),
        ),
    )


def extract_latest_annual_value_and_end_date(
    facts: dict,
    field: str,
) -> tuple[float, str | None]:
    """Extract latest annual 10-K numeric value and period end date for a field."""
    latest_record = _extract_latest_annual_record(facts, field)
    if latest_record is None:
        return math.nan, None

    try:
        value = float(latest_record.get("val"))
    except (TypeError, ValueError):
        value = math.nan
    return value, latest_record.get("end")


def extract_latest_annual_value(facts: dict, field: str) -> float:
    """Extract the latest annual 10-K value for a us-gaap field or return NaN."""
    value, _ = extract_latest_annual_value_and_end_date(facts, field)
    return value

    try:
        return float(latest_record.get("val"))
    except (TypeError, ValueError):
        return math.nan
