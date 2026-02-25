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


# Forms to include in time series: annual (10-K) and quarterly (10-Q)
TIMESERIES_FORMS = ("10-K", "10-Q")


def _get_annual_records_for_field(facts: dict, field: str) -> list[dict]:
    """Return all 10-K records for a us-gaap field (each has 'end', 'val', etc.)."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    field_payload = gaap_facts.get(field, {})
    records = _select_unit_records(field_payload)
    return [r for r in records if r.get("form") == "10-K"]


def _get_records_for_field(
    facts: dict, field: str, forms: tuple[str, ...] = TIMESERIES_FORMS
) -> list[dict]:
    """Return all records for a us-gaap field with form in forms (e.g. 10-K, 10-Q)."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    field_payload = gaap_facts.get(field, {})
    records = _select_unit_records(field_payload)
    return [r for r in records if r.get("form") in forms]


def get_all_annual_period_ends(facts: dict, fields: list[str]) -> list[str]:
    """Return sorted unique period end dates across all fields (10-K only)."""
    return get_all_period_ends(facts, fields, forms=("10-K",))


def get_all_period_ends(
    facts: dict,
    fields: list[str],
    forms: tuple[str, ...] = TIMESERIES_FORMS,
) -> list[str]:
    """Return sorted unique period end dates across all fields (10-K and 10-Q by default)."""
    ends: set[str] = set()
    for field in fields:
        for record in _get_records_for_field(facts, field, forms=forms):
            end = record.get("end")
            if end:
                ends.add(end)
    return sorted(ends, key=parse_date)


def get_values_for_period(
    facts: dict,
    period_end: str,
    fields: list[str],
    forms: tuple[str, ...] = TIMESERIES_FORMS,
) -> dict[str, float]:
    """For a given period end date, return field -> value (or NaN) from 10-K/10-Q."""
    result: dict[str, float] = {}
    for field in fields:
        value = math.nan
        for record in _get_records_for_field(facts, field, forms=forms):
            if record.get("end") == period_end:
                try:
                    value = float(record.get("val"))
                except (TypeError, ValueError):
                    pass
                break
        result[field] = value
    return result
