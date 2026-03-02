# Configuration

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SEC_USER_AGENT` | Required by SEC; set to e.g. `financial-forecast-foundation/1.0 (your@email.com)`. |
| `FRED_API_KEY` | Required for FRED API; create at https://fredaccount.stlouisfed.org/apikeys. |
| `REFERENCE_DATE` | Optional cutoff date `YYYY-MM-DD` for SEC and FRED; defaults to today if unset. |
| `REFRESH_FINANCIALS` | If set (e.g. `1`, `true`), forces rebuild of SEC financials even when output files exist. |
| `FRED_OBSERVATION_START` | Start date for FRED series (default from config). |
| `FRED_OBSERVATION_END` | End date for FRED series (optional). |

Loaded from `.env` in the project root via `python-dotenv` in `src.config`.

## Macro accounts mapping (hardcoded)

Financial columns are defined **only** in `src/config.py` by the constant **`MACRO_ACCOUNTS_MAPPING_CSV`**. It is a CSV string with columns:

- **display_name** — Column name in the pipeline outputs (e.g. `Net_Income`, `Operating_Cash_Flow`).
- **classification** — One of `P_and_L`, `Balance_sheet`, `Cash_flow`, `Other`.
- **concept** — us-gaap concept name (e.g. `NetIncomeLoss`). Multiple rows with the same `display_name` define concept aliases (first with data wins).

Config parses this into:

- **FINANCIAL_FIELDS** — Ordered list of display names (column order).
- **FINANCIAL_FIELD_CONCEPTS** — `{display_name: [concept, ...]}`.
- **FINANCIAL_FIELD_CLASSIFICATION** — `{display_name: classification}`.

There is no file-based fallback; the repo works without any `data/raw` files. To change the set of accounts or names, edit `MACRO_ACCOUNTS_MAPPING_CSV` in `src/config.py`. Optionally keep `data/raw/macro_accounts_mapping.csv` in sync for reference.

## Paths (config)

- **DATA_DIR** = `data/`
- **RAW_DATA_DIR** = `data/raw/`
- **PROCESSED_DATA_DIR** = `data/processed/`
- Output paths use **EFFECTIVE_REFERENCE_DATE_STR** in the filename (e.g. `financials_2026-01-31.parquet`).

## SEC / FRED tuning

In `src/config.py`:

- **SEC_MAX_REQUESTS_PER_SECOND** — Rate limit (default 10).
- **SEC_FETCH_MAX_WORKERS** — Parallel company fetches (default 6).
- **DEFAULT_MAX_COMPANIES** — Max companies when running from `main.py` (default 1000).
- **FRED_MAX_REQUESTS_PER_SECOND**, **FRED_FETCH_MAX_WORKERS** — FRED client limits.
