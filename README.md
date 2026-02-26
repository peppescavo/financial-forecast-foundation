# Financial Forecast Foundation

## Project Description

This project downloads financial statement data from official SEC EDGAR JSON APIs and builds standardized pandas datasets for forecasting and risk modeling.

The current pipeline builds two outputs:

- **Snapshot dataset** (`financials.parquet`): one row per company (CIK), with latest annual (`10-K`) values.
- **Time-series dataset** (`financials_timeseries.parquet`): one row per `(company, period)` using annual (`10-K`) and quarterly (`10-Q`) filings.

Both datasets include:

- `as_of_date` period end date
- static metadata from SEC submissions (`company_name`, `industry`, `region`)
- selected `us-gaap` financial fields

The pipeline persists:

- `data/processed/financials.parquet`
- `data/processed/financials_sample_max_100.xlsx` (snapshot sample, max 100 rows)
- `data/processed/financials_timeseries.parquet`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Pre-commit Setup (First Time)

Install and activate pre-commit in this repository:

```powershell
pip install pre-commit
pre-commit install
```

Run all hooks once on the full codebase:

```powershell
pre-commit run --all-files
```

What these hooks do:

- `trailing-whitespace`: removes trailing spaces.
- `end-of-file-fixer`: ensures file ends with a newline.
- `check-yaml`: validates YAML syntax.
- `check-added-large-files --maxkb=5000`: blocks very large files in commits.
- `ruff --fix`: applies fast lint fixes.
- `ruff-format`: formats code with Ruff formatter.
- `black`: applies Black formatting.

After setup, hooks run automatically on every `git commit`.

## SEC User-Agent Setup

SEC requires a valid `User-Agent` header with contact information.

Set it in PowerShell:

```powershell
$env:SEC_USER_AGENT="financial-forecast-foundation/1.0 (your_name@company.com)"
```

Or create a `.env` file in the project root:

```env
SEC_USER_AGENT="financial-forecast-foundation/1.0 (your_name@company.com)"
```

## How To Run

```bash
python main.py
```

`main.py` now builds and saves both the snapshot and time-series datasets.

## Example Usage

```python
from src.pipeline import (
    build_financials_dataframe,
    build_financials_timeseries_dataframe,
)

ciks = ["0000320193", "0000789019", "0000019617"]
ticker_lookup = {
    "0000320193": "AAPL",
    "0000789019": "MSFT",
    "0000019617": "JPM",
}
snapshot_df = build_financials_dataframe(
    ciks=ciks,
    max_companies=3,
    ticker_lookup=ticker_lookup,
)

timeseries_df = build_financials_timeseries_dataframe(
    ciks=ciks,
    max_companies=3,
    ticker_lookup=ticker_lookup,
)
```

## Snapshot Output Structure

```text
index: cik
columns:
- ticker
- as_of_date
- company_name
- industry
- region
- Revenues
- NetIncomeLoss
- Assets
- Liabilities
- StockholdersEquity
- OperatingIncomeLoss
- EBIT
- EBITDA
- CashAndCashEquivalentsAtCarryingValue
- LongTermDebt
```

## Timeseries Output Structure

```text
columns:
- cik
- ticker
- as_of_date
- company_name
- industry
- region
- Revenues
- NetIncomeLoss
- Assets
- Liabilities
- StockholdersEquity
- OperatingIncomeLoss
- EBIT
- EBITDA
- CashAndCashEquivalentsAtCarryingValue
- LongTermDebt
```

Financial values are numeric, missing data remains `NaN`, and `as_of_date` is parsed to datetime.

## Runtime Behavior

- Company fetch is parallelized with thread pool workers (`SEC_FETCH_MAX_WORKERS`, default `6`).
- SEC requests are protected by a thread-safe rate limiter (`SEC_MAX_REQUESTS_PER_SECOND`, default `10`).
- Each company pull fetches both `submissions` (metadata) and `companyfacts` (XBRL financials).

## Architecture

- `src/config.py`: constants, SEC endpoints, headers, field list, path definitions.
- `src/edgar_client.py`: SEC CIK/ticker universe helpers, thread-safe rate-limited API retrieval, and combined submissions/facts fetch.
- `src/xbrl_parser.py`: extraction of latest annual values plus period/value utilities for 10-K/10-Q time-series assembly.
- `src/financials.py`: single-company snapshot record and multi-period time-series record builders.
- `src/pipeline.py`: parallel multi-company orchestration, snapshot/time-series DataFrame construction, type coercion, parquet persistence, and snapshot Excel export.
- `src/utils.py`: logging setup, environment loading, and filesystem helpers.
- `main.py`: orchestration entrypoint that runs both pipelines.
- `tests/test_pipeline.py`: pytest coverage for snapshot and time-series pipeline shapes and persistence.
