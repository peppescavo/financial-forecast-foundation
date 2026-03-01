"""Configuration for SEC EDGAR financial statement pipeline."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


# Optional reference date (YYYY-MM-DD). If unset, pipelines collect up to today.
# You can set it here or via the environment variable REFERENCE_DATE.
REFERENCE_DATE: str | None = "2026-01-31"
_reference_date_env = os.getenv("REFERENCE_DATE", "").strip()
if _reference_date_env:
    REFERENCE_DATE = _reference_date_env

_today = date.today()
_reference_date_value = _parse_iso_date(REFERENCE_DATE)
if _reference_date_value and _reference_date_value > _today:
    _reference_date_value = _today

EFFECTIVE_REFERENCE_DATE = _reference_date_value or _today
EFFECTIVE_REFERENCE_DATE_STR = EFFECTIVE_REFERENCE_DATE.isoformat()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_FINANCIALS_PATH = (
    PROCESSED_DATA_DIR / f"financials_{EFFECTIVE_REFERENCE_DATE_STR}.parquet"
)
PROCESSED_FINANCIALS_TIMESERIES_PATH = (
    PROCESSED_DATA_DIR / f"financials_timeseries_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)
PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH = (
    PROCESSED_DATA_DIR
    / f"financials_timeseries_delta_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)
SAMPLE_MAX_ROWS = 1000
PROCESSED_FINANCIALS_SAMPLE_PATH = (
    PROCESSED_DATA_DIR
    / f"financials_sample_max_{SAMPLE_MAX_ROWS}_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)

# Macroeconomic data (FRED)
PROCESSED_MACRO_WIDE_PATH = (
    PROCESSED_DATA_DIR / f"macro_timeseries_wide_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_TICKER_MAPPING_URL = "https://www.sec.gov/files/company_tickers.json"

SEC_TIMEOUT_SECONDS = 30
# SEC allows 10 requests/second; rate limiter used when fetching in parallel
SEC_MAX_REQUESTS_PER_SECOND = 10
SEC_FETCH_MAX_WORKERS = 6  # parallel company fetches (each company = 2 requests)
DEFAULT_MAX_COMPANIES = 1000

SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "financial-forecast-foundation/1.0 (quant-team@example.com)",
)

SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept": "application/json",
}

# FRED requires an API key for requests. Create one at:
# https://fredaccount.stlouisfed.org/apikeys
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_SERIES_OBSERVATIONS_URL = f"{FRED_BASE_URL}/series/observations"
FRED_SERIES_URL = f"{FRED_BASE_URL}/series"

FRED_TIMEOUT_SECONDS = 30
FRED_MAX_REQUESTS_PER_SECOND = 5
FRED_FETCH_MAX_WORKERS = 6

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Default observation window for macro downloads (override via env vars if needed)
FRED_OBSERVATION_START = os.getenv("FRED_OBSERVATION_START", "1990-01-01")
FRED_OBSERVATION_END = os.getenv("FRED_OBSERVATION_END", "")

# Default macro series to download for balance-sheet / income-statement modeling.
# Keys are FRED series IDs: https://fred.stlouisfed.org/
FRED_DEFAULT_SERIES: dict[str, str] = {
    "GDPC1": "Real Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index (CPI-U)",
    "PCEPI": "Personal Consumption Expenditures Price Index",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DGS2": "2-Year Treasury Constant Maturity Rate",
    "DGS3MO": "3-Month Treasury Constant Maturity Rate",
    "T10Y2Y": "10Y-2Y Treasury Yield Spread",
    "BAA": "Moody's Seasoned Baa Corporate Bond Yield",
    "AAA": "Moody's Seasoned Aaa Corporate Bond Yield",
    "INDPRO": "Industrial Production Index",
    "RSAFS": "Retail Sales",
    "UMCSENT": "University of Michigan: Consumer Sentiment",
    "HOUST": "Housing Starts",
    "SP500": "S&P 500",
    "VIXCLS": "CBOE Volatility Index (VIX)",
    "DCOILWTICO": "Crude Oil Prices: WTI",
    "M2SL": "M2 Money Stock",
    "DTWEXBGS": "Trade Weighted U.S. Dollar Index: Broad",
}

FINANCIAL_FIELDS_DEFAULT = [
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

# Curated macro list from discovery (scripts/discover_us_gaap_concepts.py).
# If present, FINANCIAL_FIELDS is loaded from it; else FINANCIAL_FIELDS_DEFAULT is used.
MACRO_FINANCIAL_CONCEPTS_PATH = RAW_DATA_DIR / "macro_financial_concepts.json"

if MACRO_FINANCIAL_CONCEPTS_PATH.exists():
    with open(MACRO_FINANCIAL_CONCEPTS_PATH) as f:
        _loaded = json.load(f)
    FINANCIAL_FIELDS = (
        list(_loaded) if isinstance(_loaded, list) else FINANCIAL_FIELDS_DEFAULT
    )
else:
    FINANCIAL_FIELDS = FINANCIAL_FIELDS_DEFAULT.copy()

# Map output field names to one or more us-gaap concept names to try (first with data wins).
# SEC companyfacts uses exact taxonomy concept names; EBITDA/EBIT are often missing or use longer names.
FINANCIAL_FIELD_CONCEPTS: dict[str, list[str]] = {
    "EBIT": [
        "EBIT",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "EBITDA": [
        "EBITDA",
        "EarningsBeforeInterestTaxesDepreciationAndAmortization",
    ],
}
# All other FINANCIAL_FIELDS use the field name as the single us-gaap concept.

# Static company metadata from SEC submissions (name, industry, region only)
SUBMISSION_STATIC_FIELDS = ["company_name", "industry", "region"]
