"""Company-level financial statement record builder."""

from __future__ import annotations

import logging
import math

from src.config import FINANCIAL_FIELDS, SUBMISSION_STATIC_FIELDS
from src.edgar_client import fetch_company_submissions_and_facts, normalize_cik
from src.utils import parse_date
from src.xbrl_parser import (
    extract_latest_annual_value_and_end_date,
    get_all_period_ends,
    get_values_for_period,
)

logger = logging.getLogger(__name__)


def _parse_submissions_static(submissions: dict) -> dict[str, str | float]:
    """Extract name, industry, and region from SEC submissions JSON."""
    addr = (submissions.get("addresses") or {}).get("business") or {}
    record: dict[str, str | float] = {k: "" for k in SUBMISSION_STATIC_FIELDS}
    record["company_name"] = submissions.get("name") or ""
    record["industry"] = submissions.get("sicDescription") or ""
    record["region"] = (
        addr.get("stateOrCountry") or addr.get("country") or ""
    ).strip() or (submissions.get("stateOfIncorporation") or "")
    return record


def build_company_financials(
    cik: str,
    ticker: str | None = None,
    reference_date: str | None = None,
) -> dict[str, str | float]:
    """Build a single counterparty financial record for the latest annual period."""
    normalized_cik = normalize_cik(cik)
    normalized_ticker = ticker.strip().upper() if ticker else math.nan
    record: dict[str, str | float] = {
        "cik": normalized_cik,
        "ticker": normalized_ticker,
        "as_of_date": math.nan,
    }
    for field in SUBMISSION_STATIC_FIELDS:
        record[field] = ""
    for field in FINANCIAL_FIELDS:
        record[field] = math.nan

    try:
        submissions, facts = fetch_company_submissions_and_facts(normalized_cik)
        for key, value in _parse_submissions_static(submissions).items():
            record[key] = value

        latest_period_end: str | None = None
        for field in FINANCIAL_FIELDS:
            value, period_end = extract_latest_annual_value_and_end_date(
                facts, field, reference_date=reference_date
            )
            record[field] = value
            if period_end and parse_date(period_end) > parse_date(
                latest_period_end or ""
            ):
                latest_period_end = period_end
        record["as_of_date"] = latest_period_end if latest_period_end else math.nan
    except Exception:
        logger.exception(
            "Failed to build financials for cik=%s ticker=%s",
            normalized_cik,
            normalized_ticker,
        )
        for field in FINANCIAL_FIELDS:
            record[field] = math.nan

    return record


def build_company_financials_timeseries(
    cik: str,
    ticker: str | None = None,
    reference_date: str | None = None,
) -> list[dict[str, str | float]]:
    """Build one record per period for a company: full time series (10-K annual + 10-Q quarterly)."""
    normalized_cik = normalize_cik(cik)
    normalized_ticker = ticker.strip().upper() if ticker else math.nan
    static: dict[str, str | float] = {
        "cik": normalized_cik,
        "ticker": normalized_ticker,
        **{k: "" for k in SUBMISSION_STATIC_FIELDS},
    }

    try:
        submissions, facts = fetch_company_submissions_and_facts(normalized_cik)
        for key, value in _parse_submissions_static(submissions).items():
            static[key] = value

        period_ends = get_all_period_ends(facts, FINANCIAL_FIELDS)
        if not period_ends:
            return []

        if reference_date:
            cutoff = parse_date(reference_date)
            period_ends = [
                period_end
                for period_end in period_ends
                if parse_date(period_end) <= cutoff
            ]
            if not period_ends:
                return []

        records = []
        for period_end in period_ends:
            values = get_values_for_period(facts, period_end, FINANCIAL_FIELDS)
            row = {
                **static,
                "as_of_date": period_end,
                **values,
            }
            records.append(row)
        return records
    except Exception:
        logger.exception(
            "Failed to build financials timeseries for cik=%s ticker=%s",
            normalized_cik,
            normalized_ticker,
        )
        return []
