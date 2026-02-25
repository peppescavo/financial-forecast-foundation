"""Company-level financial statement record builder."""

from __future__ import annotations

import logging
import math

from src.config import FINANCIAL_FIELDS
from src.edgar_client import fetch_company_facts, normalize_cik
from src.utils import parse_date
from src.xbrl_parser import extract_latest_annual_value_and_end_date

logger = logging.getLogger(__name__)


def build_company_financials(cik: str, ticker: str | None = None) -> dict[str, str | float]:
    """Build a single counterparty financial record for the latest annual period."""
    normalized_cik = normalize_cik(cik)
    normalized_ticker = ticker.strip().upper() if ticker else math.nan
    record: dict[str, str | float] = {
        "cik": normalized_cik,
        "ticker": normalized_ticker,
        "as_of_date": math.nan,
    }

    try:
        facts = fetch_company_facts(normalized_cik)
        latest_period_end: str | None = None
        for field in FINANCIAL_FIELDS:
            value, period_end = extract_latest_annual_value_and_end_date(facts, field)
            record[field] = value
            if period_end and parse_date(period_end) > parse_date(latest_period_end):
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
