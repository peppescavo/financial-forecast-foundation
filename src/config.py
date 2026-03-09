"""Configuration for SEC EDGAR financial statement pipeline."""

from __future__ import annotations

import csv
import io
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
PROCESSED_MACRO_QUARTERLY_WIDE_PATH = (
    PROCESSED_DATA_DIR
    / f"macro_timeseries_quarterly_wide_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)
PROCESSED_MACRO_QUARTERLY_DELTA_PATH = (
    PROCESSED_DATA_DIR
    / f"macro_timeseries_quarterly_delta_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)
PROCESSED_MACRO_QUARTERLY_WIDE_MEAN_PATH = (
    PROCESSED_DATA_DIR
    / f"macro_timeseries_quarterly_wide_mean_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)
PROCESSED_MACRO_QUARTERLY_DELTA_MEAN_PATH = (
    PROCESSED_DATA_DIR
    / f"macro_timeseries_quarterly_delta_mean_{EFFECTIVE_REFERENCE_DATE_STR}.xlsx"
)

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_TICKER_MAPPING_URL = "https://www.sec.gov/files/company_tickers.json"

SEC_TIMEOUT_SECONDS = 30
# SEC allows 10 requests/second; rate limiter used when fetching in parallel
SEC_MAX_REQUESTS_PER_SECOND = 10
SEC_FETCH_MAX_WORKERS = 6  # parallel company fetches (each company = 2 requests)
DEFAULT_MAX_COMPANIES = 5000

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

# Curated macro accounts: display names and classification (P_and_L, Balance_sheet, Cash_flow, Other).
# Hardcoded so the repo works without data/raw; keep in sync with data/raw/macro_accounts_mapping.csv when editing.
MACRO_ACCOUNTS_MAPPING_CSV = """\
display_name,classification,concept
Revenues,P_and_L,Revenues
Cost_Of_Revenue,P_and_L,CostOfRevenue
Gross_Profit,P_and_L,GrossProfit
Operating_Income,P_and_L,OperatingIncomeLoss
EBIT,P_and_L,EBIT
EBIT,P_and_L,IncomeLossFromContinuingOperationsBeforeIncomeTaxes
EBIT,P_and_L,IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest
EBITDA,P_and_L,EBITDA
EBITDA,P_and_L,EarningsBeforeInterestTaxesDepreciationAndAmortization
Interest_Expense,P_and_L,InterestExpense
Interest_Income,P_and_L,InterestIncome
Income_Tax_Expense,P_and_L,IncomeTaxExpenseBenefit
Net_Income,P_and_L,NetIncomeLoss
Net_Income_Attributable,P_and_L,NetIncomeLossAttributableToParent
Comprehensive_Income,P_and_L,ComprehensiveIncomeNetOfTax
Depreciation_And_Amortization,P_and_L,DepreciationDepletionAndAmortization
Depreciation_And_Amortization,P_and_L,DepreciationAndAmortization
R_and_D_Expense,P_and_L,ResearchAndDevelopmentExpense
SG_and_A_Expense,P_and_L,SellingGeneralAndAdministrativeExpense
Share_Based_Compensation,P_and_L,ShareBasedCompensation
Income_From_Equity_Investments,P_and_L,IncomeLossFromEquityMethodInvestments
Other_Comprehensive_Income,P_and_L,OtherComprehensiveIncomeLossNetOfTax
Assets,Balance_sheet,Assets
Assets_Current,Balance_sheet,AssetsCurrent
Assets_Noncurrent,Balance_sheet,AssetsNoncurrent
Liabilities,Balance_sheet,Liabilities
Liabilities_Current,Balance_sheet,LiabilitiesCurrent
Liabilities_Noncurrent,Balance_sheet,LiabilitiesNoncurrent
Stockholders_Equity,Balance_sheet,StockholdersEquity
Liabilities_And_Equity,Balance_sheet,LiabilitiesAndStockholdersEquity
Cash_And_Equivalents,Balance_sheet,CashAndCashEquivalentsAtCarryingValue
Cash_And_Equivalents,Balance_sheet,CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents
Inventory,Balance_sheet,InventoryNet
Receivables_Net,Balance_sheet,AccountsReceivableNetCurrent
PPE_Net,Balance_sheet,PropertyPlantAndEquipmentNet
Goodwill,Balance_sheet,Goodwill
Intangibles_Net,Balance_sheet,IntangibleAssetsNetExcludingGoodwill
Intangibles_Net,Balance_sheet,FiniteLivedIntangibleAssetsNet
Accounts_Payable,Balance_sheet,AccountsPayableCurrent
Long_Term_Debt,Balance_sheet,LongTermDebt
Long_Term_Debt_Current,Balance_sheet,LongTermDebtCurrent
Deferred_Tax_Assets_Net,Balance_sheet,DeferredTaxAssetsNet
Deferred_Tax_Liabilities,Balance_sheet,DeferredTaxLiabilities
Deferred_Tax_Liabilities_Net,Balance_sheet,DeferredTaxAssetsLiabilitiesNet
Retained_Earnings,Balance_sheet,RetainedEarningsAccumulatedDeficit
Operating_Lease_Assets,Balance_sheet,OperatingLeaseRightOfUseAsset
Operating_Lease_Liability,Balance_sheet,OperatingLeaseLiability
AOCI_Net_Of_Tax,Balance_sheet,AccumulatedOtherComprehensiveIncomeLossNetOfTax
Operating_Cash_Flow,Cash_flow,NetCashProvidedByUsedInOperatingActivities
Investing_Cash_Flow,Cash_flow,NetCashProvidedByUsedInInvestingActivities
Financing_Cash_Flow,Cash_flow,NetCashProvidedByUsedInFinancingActivities
CapEx,Cash_flow,PaymentsToAcquirePropertyPlantAndEquipment
Payments_For_Repurchase,Cash_flow,PaymentsForRepurchaseOfCommonStock
Proceeds_From_Debt,Cash_flow,ProceedsFromLongTermDebt
Repayments_Of_Debt,Cash_flow,RepaymentsOfLongTermDebt
Dividends_Paid,Cash_flow,PaymentsOfDividends
Shares_Basic,Other,WeightedAverageNumberOfSharesOutstandingBasic
Shares_Diluted,Other,WeightedAverageNumberOfDilutedSharesOutstanding
EPS_Basic,Other,EarningsPerShareBasic
EPS_Diluted,Other,EarningsPerShareDiluted
"""

_display_order: list[str] = []
_concepts_by_display: dict[str, list[str]] = {}
_classification_by_display: dict[str, str] = {}
for row in csv.DictReader(io.StringIO(MACRO_ACCOUNTS_MAPPING_CSV)):
    display_name = (row.get("display_name") or "").strip()
    concept = (row.get("concept") or "").strip()
    classification = (row.get("classification") or "").strip() or "Other"
    if not display_name or not concept:
        continue
    if display_name not in _concepts_by_display:
        _display_order.append(display_name)
        _concepts_by_display[display_name] = []
        _classification_by_display[display_name] = classification
    _concepts_by_display[display_name].append(concept)

FINANCIAL_FIELDS = _display_order
FINANCIAL_FIELD_CONCEPTS = _concepts_by_display
FINANCIAL_FIELD_CLASSIFICATION = _classification_by_display

# Static company metadata from SEC submissions (name, industry, region only)
SUBMISSION_STATIC_FIELDS = ["company_name", "industry", "region"]
