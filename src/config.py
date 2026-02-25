"""Configuration for SEC EDGAR financial statement pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_FINANCIALS_PATH = PROCESSED_DATA_DIR / "financials.parquet"
SAMPLE_MAX_ROWS = 100
PROCESSED_FINANCIALS_SAMPLE_PATH = (
    PROCESSED_DATA_DIR / f"financials_sample_max_{SAMPLE_MAX_ROWS}.xlsx"
)

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_TICKER_MAPPING_URL = "https://www.sec.gov/files/company_tickers.json"

SEC_TIMEOUT_SECONDS = 30
# SEC allows 10 requests/second; rate limiter used when fetching in parallel
SEC_MAX_REQUESTS_PER_SECOND = 10
SEC_FETCH_MAX_WORKERS = 6  # parallel company fetches (each company = 2 requests)
DEFAULT_MAX_COMPANIES = 100

SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "financial-forecast-foundation/1.0 (quant-team@example.com)",
)

SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept": "application/json",
}

FINANCIAL_FIELDS = [
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

# Static company metadata from SEC submissions (name, industry, region only)
SUBMISSION_STATIC_FIELDS = ["company_name", "industry", "region"]
