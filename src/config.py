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
PROCESSED_FINANCIALS_TIMESERIES_PATH = (
    PROCESSED_DATA_DIR / "financials_timeseries.parquet"
)
SAMPLE_MAX_ROWS = 1000
PROCESSED_FINANCIALS_SAMPLE_PATH = (
    PROCESSED_DATA_DIR / f"financials_sample_max_{SAMPLE_MAX_ROWS}.xlsx"
)

# Macroeconomic data (FRED)
PROCESSED_MACRO_LONG_PATH = PROCESSED_DATA_DIR / "macro_timeseries_long.parquet"
PROCESSED_MACRO_WIDE_PATH = PROCESSED_DATA_DIR / "macro_timeseries_wide.parquet"

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
