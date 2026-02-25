# Financial Forecast Foundation

## Project Description

This project downloads financial statement data from official SEC EDGAR JSON APIs and builds a standardized pandas DataFrame that can be used as a foundation layer for macro time-series forecasting and risk modeling. Each row represents one company identified by CIK, and each column represents a selected `us-gaap` field using the most recent annual (`10-K`) value. The output includes an `as_of_date` column with the latest annual period-end date available for each company.

The pipeline also persists the modeling-ready output to:

- `data/processed/financials.parquet`
- `data/processed/financials_sample_max_1000.xlsx` (snapshot sample, max 1000 rows)

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

## Example Usage

```python
from src.pipeline import build_financials_dataframe

ciks = ["0000320193", "0000789019", "0000019617"]
ticker_lookup = {
    "0000320193": "AAPL",
    "0000789019": "MSFT",
    "0000019617": "JPM",
}
df = build_financials_dataframe(ciks=ciks, max_companies=3, ticker_lookup=ticker_lookup)
```

## Example Output Structure

```text
index: cik
columns:
- ticker
- as_of_date
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

Values are numeric, missing data remains `NaN`, and the DataFrame is directly usable for modeling pipelines.

## Architecture

- `src/config.py`: constants, SEC endpoints, headers, field list, path definitions.
- `src/edgar_client.py`: SEC CIK/ticker universe helpers and SEC API retrieval with rate limiting.
- `src/xbrl_parser.py`: extraction of most recent annual `10-K` values from `companyfacts`.
- `src/financials.py`: single-company financial record assembly keyed by CIK.
- `src/pipeline.py`: multi-company orchestration, DataFrame construction, numeric coercion, parquet persistence, and Excel sample snapshot export.
- `src/utils.py`: logging setup, environment loading, and filesystem helpers.
- `main.py`: minimal orchestration entrypoint.
- `tests/test_pipeline.py`: minimal real pytest coverage for pipeline output shape.
