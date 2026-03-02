# Module reference

## src.config

Central configuration: paths, API endpoints, rate limits, and the **macro accounts mapping**.

- **Paths** — `PROJECT_ROOT`, `DATA_DIR`, `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`; `PROCESSED_FINANCIALS_PATH`, `PROCESSED_FINANCIALS_TIMESERIES_PATH`, `PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH`, `PROCESSED_FINANCIALS_SAMPLE_PATH`, `PROCESSED_MACRO_WIDE_PATH`.
- **Reference date** — `REFERENCE_DATE` (env or default), `EFFECTIVE_REFERENCE_DATE`, `EFFECTIVE_REFERENCE_DATE_STR` (used in output filenames).
- **SEC** — `SEC_*` URLs, headers, `SEC_USER_AGENT`, `SEC_MAX_REQUESTS_PER_SECOND`, `SEC_FETCH_MAX_WORKERS`, `DEFAULT_MAX_COMPANIES`.
- **FRED** — `FRED_*` URLs, `FRED_API_KEY`, `FRED_DEFAULT_SERIES`, observation window.
- **Financial fields** — `MACRO_ACCOUNTS_MAPPING_CSV` (hardcoded CSV string); parsed into `FINANCIAL_FIELDS` (display names), `FINANCIAL_FIELD_CONCEPTS` (display_name → list of us-gaap concepts), `FINANCIAL_FIELD_CLASSIFICATION` (display_name → P_and_L | Balance_sheet | Cash_flow | Other).
- **Metadata** — `SUBMISSION_STATIC_FIELDS`: `company_name`, `industry`, `region`.

## src.edgar_client

SEC EDGAR API client: rate-limited GET, CIK/ticker helpers, fetch submissions and companyfacts.

- **Rate limiting** — `_sec_get(url)` enforces `SEC_MAX_REQUESTS_PER_SECOND` (thread-safe).
- **CIK/ticker** — `ticker_to_cik()`, `normalize_cik()`, `fetch_cik_universe_with_tickers()`.
- **Fetch** — `fetch_company_submissions(cik)`, `fetch_company_facts(cik)`, `fetch_company_submissions_and_facts(cik)`.

## src.xbrl_parser

Extract normalized financial values from SEC companyfacts (us-gaap).

- **Concept resolution** — Uses `config.FINANCIAL_FIELD_CONCEPTS` to map each display field to one or more us-gaap concept names; first concept with data wins.
- **Snapshot** — `extract_latest_annual_value()`, `extract_latest_annual_value_and_end_date()` (latest 10-K; optional reference date).
- **Timeseries** — `get_all_period_ends()`, `get_values_for_period()` (10-K and 10-Q).
- **Derived EBITDA** — When no reported EBITDA concept exists, computes OperatingIncomeLoss + DepreciationAndAmortization (or fallback D&amp;A concepts).
- **Units** — Prefers USD; otherwise first available unit.

## src.financials

Build per-company records from SEC data.

- **Snapshot** — `build_company_financials(cik, ticker=None, reference_date=None)` → single dict (cik, ticker, as_of_date, metadata, and all `FINANCIAL_FIELDS`).
- **Timeseries** — `build_company_financials_timeseries(cik, ticker=None, reference_date=None)` → list of dicts (one per period).
- Uses `edgar_client.fetch_company_submissions_and_facts()` and `xbrl_parser` for extraction.

## src.pipeline

Orchestrate multi-company SEC financials: parallel fetch, DataFrame build, persistence.

- **Snapshot** — `build_financials_dataframe(ciks, max_companies, ticker_lookup=None, reference_date=None)` → DataFrame (index cik), writes parquet + sample Excel.
- **Timeseries** — `build_financials_timeseries_dataframe(...)` → DataFrame, writes Excel; `build_financials_timeseries_delta_dataframe(ts_df)` → delta DataFrame; `persist_financials_timeseries_delta_dataframe(delta_df)`.
- Uses `ThreadPoolExecutor` with `SEC_FETCH_MAX_WORKERS`; columns = metadata + `FINANCIAL_FIELDS` (display names from config).

## src.macro_pipeline

FRED macro series download and wide-format Excel.

- **Entry** — `build_and_persist_macro_timeseries()` → (long DataFrame, wide DataFrame), writes wide to `PROCESSED_MACRO_WIDE_PATH`.
- Uses `fred_client` and `FRED_DEFAULT_SERIES`; observation window from config or `REFERENCE_DATE`.

## src.fred_client

FRED API client: rate-limited requests, series observations.

- **Fetch** — Get observations for given series IDs; thread-safe rate limiting.
- Requires `FRED_API_KEY` in config (env or .env).

## src.discover_concepts

Discovery and curation of us-gaap concepts from companyfacts (used by the CLI script, not by the main pipeline).

- **Discovery** — `concepts_reported_for_facts(facts)` (set of concept names with 10-K/10-Q USD); `run_discovery(max_companies, output_path)` → writes coverage JSON + analysis CSV.
- **Curation** — `run_curate(min_pct, coverage_path, output_path)` → reads coverage, applies filters, merges core fields, writes curated list JSON.
- **Outputs** — `data/raw/us_gaap_concept_coverage.json`, `data/raw/us_gaap_concepts_for_analysis.csv`, `data/raw/macro_financial_concepts.json` (not used by config anymore; mapping is hardcoded).

## src.utils

- **Environment** — `initialize_environment()` (creates data dirs).
- **Logging** — `configure_logging(level)`.
- **Helpers** — `ensure_directory(path)`, `parse_date()` (used by xbrl_parser).

## main.py

Entrypoint: `main()` runs logging + env init; then SEC financials (snapshot, timeseries, delta) and FRED macro pipeline. Uses `REFRESH_FINANCIALS` env to force rebuild; otherwise skips if output files exist.

## scripts.discover_us_gaap_concepts

CLI for discovery and curation: `--max-companies`, `--output`, `--curate`, `--min-pct`, `--coverage`. Delegates to `src.discover_concepts`.
