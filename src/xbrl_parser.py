"""Parsers for extracting normalized financial fields from SEC companyfacts."""

from __future__ import annotations

import math

from src import config
from src.utils import parse_date


def _get_concepts_for_field(field: str) -> list[str]:
    """Return us-gaap concept names to try for this output field (first with data wins)."""
    return config.FINANCIAL_FIELD_CONCEPTS.get(field, [field])


def _select_unit_records(field_payload: dict) -> list[dict]:
    """Select preferred units records for a us-gaap field payload."""
    units = field_payload.get("units", {})
    if "USD" in units:
        return units["USD"]
    for records in units.values():
        return records
    return []


def _extract_latest_annual_record_for_concept(
    facts: dict, concept: str, reference_date: str | None = None
) -> dict | None:
    """Extract the latest annual 10-K record for a single us-gaap concept."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    field_payload = gaap_facts.get(concept, {})
    records = _select_unit_records(field_payload)

    annual_records = [
        record
        for record in records
        if record.get("form") == "10-K" and record.get("end")
    ]
    if reference_date:
        cutoff = parse_date(reference_date)
        annual_records = [
            record
            for record in annual_records
            if parse_date(record.get("end")) <= cutoff
        ]
    if not annual_records:
        return None

    return max(
        annual_records,
        key=lambda record: (
            parse_date(record.get("end")),
            parse_date(record.get("filed")),
        ),
    )


def _extract_latest_annual_record(
    facts: dict, field: str, reference_date: str | None = None
) -> dict | None:
    """Extract the latest annual 10-K record for a us-gaap field (tries concept aliases)."""
    for concept in _get_concepts_for_field(field):
        record = _extract_latest_annual_record_for_concept(
            facts, concept, reference_date=reference_date
        )
        if record is not None:
            return record
    return None


def extract_latest_annual_value_and_end_date(
    facts: dict,
    field: str,
    reference_date: str | None = None,
) -> tuple[float, str | None]:
    """Extract latest annual 10-K numeric value and period end date for a field."""
    latest_record = _extract_latest_annual_record(
        facts, field, reference_date=reference_date
    )
    if latest_record is None:
        if field == "EBITDA":
            value, period_end = _derived_ebitda_latest_annual(facts, reference_date)
            return value, period_end
        return math.nan, None

    try:
        value = float(latest_record.get("val"))
    except (TypeError, ValueError):
        value = math.nan
    if field == "EBITDA" and math.isnan(value):
        value, period_end = _derived_ebitda_latest_annual(facts, reference_date)
        return value, period_end or latest_record.get("end")
    return value, latest_record.get("end")


def _derived_ebitda_latest_annual(
    facts: dict, reference_date: str | None = None
) -> tuple[float, str | None]:
    """Compute latest annual EBITDA as OperatingIncomeLoss + D&A when not reported."""
    records = _get_records_for_concept(
        facts, _DERIVED_EBITDA_OPERATING_CONCEPT, forms=("10-K",)
    )
    annual_ends = sorted(
        {r.get("end") for r in records if r.get("end")},
        key=parse_date,
        reverse=True,
    )
    if reference_date:
        cutoff = parse_date(reference_date)
        annual_ends = [e for e in annual_ends if parse_date(e) <= cutoff]
    if not annual_ends:
        return math.nan, None
    period_end = annual_ends[0]
    value = _compute_derived_ebitda_for_period(facts, period_end, forms=("10-K",))
    return value, period_end if not math.isnan(value) else None


def extract_latest_annual_value(
    facts: dict, field: str, reference_date: str | None = None
) -> float:
    """Extract the latest annual 10-K value for a us-gaap field or return NaN."""
    value, _ = extract_latest_annual_value_and_end_date(
        facts, field, reference_date=reference_date
    )
    return value


# Forms to include in time series: annual (10-K) and quarterly (10-Q)
TIMESERIES_FORMS = ("10-K", "10-Q")

# Concepts used to derive EBITDA when not reported: OperatingIncome + D&A
_DERIVED_EBITDA_OPERATING_CONCEPT = "OperatingIncomeLoss"
_DERIVED_EBITDA_DA_CONCEPTS = [
    "DepreciationAndAmortization",
    "DepreciationDepletionAndAmortization",
    "DepreciationAmortizationAndAccretionNet",
]


def _get_value_for_concept_at_period(
    facts: dict,
    period_end: str,
    concept: str,
    forms: tuple[str, ...] = TIMESERIES_FORMS,
) -> float:
    """Return numeric value for a single us-gaap concept at period_end, or NaN."""
    for record in _get_records_for_concept(facts, concept, forms=forms):
        if record.get("end") == period_end:
            try:
                return float(record.get("val"))
            except (TypeError, ValueError):
                pass
    return math.nan


def _compute_derived_ebitda_for_period(
    facts: dict,
    period_end: str,
    forms: tuple[str, ...] = TIMESERIES_FORMS,
) -> float:
    """Compute EBITDA as OperatingIncomeLoss + D&A for the period when not reported."""
    operating = _get_value_for_concept_at_period(
        facts, period_end, _DERIVED_EBITDA_OPERATING_CONCEPT, forms=forms
    )
    if math.isnan(operating):
        return math.nan
    da = math.nan
    for concept in _DERIVED_EBITDA_DA_CONCEPTS:
        da = _get_value_for_concept_at_period(facts, period_end, concept, forms=forms)
        if not math.isnan(da):
            break
    if math.isnan(da):
        return math.nan
    return operating + da


def _get_records_for_concept(
    facts: dict, concept: str, forms: tuple[str, ...] = TIMESERIES_FORMS
) -> list[dict]:
    """Return all records for a single us-gaap concept with form in forms."""
    gaap_facts = facts.get("facts", {}).get("us-gaap", {})
    field_payload = gaap_facts.get(concept, {})
    records = _select_unit_records(field_payload)
    return [r for r in records if r.get("form") in forms]


def _get_annual_records_for_field(facts: dict, field: str) -> list[dict]:
    """Return all 10-K records for a us-gaap field (tries concept aliases)."""
    for concept in _get_concepts_for_field(field):
        records = _get_records_for_concept(facts, concept, forms=("10-K",))
        if records:
            return records
    return []


def _get_records_for_field(
    facts: dict, field: str, forms: tuple[str, ...] = TIMESERIES_FORMS
) -> list[dict]:
    """Return all records for a us-gaap field with form in forms (tries concept aliases)."""
    for concept in _get_concepts_for_field(field):
        records = _get_records_for_concept(facts, concept, forms=forms)
        if records:
            return records
    return []


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
    if "EBITDA" in fields and math.isnan(result.get("EBITDA", math.nan)):
        result["EBITDA"] = _compute_derived_ebitda_for_period(
            facts, period_end, forms=forms
        )
    return result
