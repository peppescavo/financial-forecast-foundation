"""Company-level financial statement record builder."""

from __future__ import annotations

import logging
import math

from src.config import FINANCIAL_FIELDS
from src.edgar_client import fetch_company_facts, ticker_to_cik
from src.xbrl_parser import extract_latest_annual_value

logger = logging.getLogger(__name__)


def build_company_financials(ticker: str) -> dict[str, str | float]:
    """Build a single counterparty financial record for the latest annual period."""
    normalized = ticker.strip().upper()
    record: dict[str, str | float] = {"ticker": normalized}

    try:
        cik = ticker_to_cik(normalized)
        facts = fetch_company_facts(cik)
        for field in FINANCIAL_FIELDS:
            record[field] = extract_latest_annual_value(facts, field)
    except Exception:
        logger.exception("Failed to build financials for ticker=%s", normalized)
        for field in FINANCIAL_FIELDS:
            record[field] = math.nan

    return record