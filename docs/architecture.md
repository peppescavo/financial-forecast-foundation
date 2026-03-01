# Architecture

## Overview

The project builds two kinds of outputs:

1. **SEC financials** — Snapshot (one row per company) and time-series (one row per company-period) from SEC EDGAR companyfacts (XBRL).
2. **FRED macro** — Wide-format time-series of macroeconomic indicators from the FRED API.

Financial columns are defined by a **hardcoded macro accounts mapping** in config (54 accounts with readable display names and classification: P&amp;L, Balance sheet, Cash flow, Other).

## Data flow

```
SEC EDGAR                          FRED API
     │                                  │
     ▼                                  ▼
edgar_client  ──► companyfacts    fred_client  ──► series observations
     │            (submissions)         │
     ▼                                  ▼
xbrl_parser   ──► extract values   macro_pipeline  ──► wide Excel
     │            (10-K / 10-Q)           │
     ▼                                  │
financials    ──► per-company records   │
     │                                  │
     ▼                                  ▼
pipeline      ──► DataFrame ──► parquet / Excel   macro_timeseries_wide_*.xlsx
                   snapshot
                   timeseries
                   timeseries_delta
```

## Pipeline (SEC financials)

1. **Universe** — `edgar_client.fetch_cik_universe_with_tickers()` gets all CIKs (or a subset).
2. **Fetch** — For each CIK, `fetch_company_submissions_and_facts()` returns submissions (metadata) and companyfacts (us-gaap concepts and facts).
3. **Parse** — `xbrl_parser` resolves each display field to one or more us-gaap concepts (aliases), extracts latest annual or period-level values, and derives EBITDA when missing (OperatingIncome + D&amp;A).
4. **Build** — `financials.build_company_financials()` produces one snapshot record; `build_company_financials_timeseries()` produces one record per period.
5. **Aggregate** — `pipeline` runs these in parallel (ThreadPoolExecutor), builds DataFrames, coerces types, and persists parquet + Excel (snapshot sample, timeseries, timeseries delta).

## Macro pipeline (FRED)

1. **Config** — `FRED_DEFAULT_SERIES` and optional `FRED_OBSERVATION_START` / `FRED_OBSERVATION_END` (or `REFERENCE_DATE`).
2. **Fetch** — `fred_client` downloads observations per series with rate limiting.
3. **Persist** — `macro_pipeline.build_and_persist_macro_timeseries()` writes long and wide Excel to `data/processed/macro_timeseries_wide_<date>.xlsx`.

## Discovery (optional)

- **scripts/discover_us_gaap_concepts.py** — Fetches companyfacts for N companies, aggregates which us-gaap concepts appear (10-K/10-Q, USD), writes `data/raw/us_gaap_concept_coverage.json` and `data/raw/us_gaap_concepts_for_analysis.csv`.
- **Curate** — `--curate` reads the coverage file, applies min-pct and name filters, merges core fields, writes `data/raw/macro_financial_concepts.json`. The main pipeline does **not** use these files; it uses the **hardcoded** mapping in `src/config.py` (`MACRO_ACCOUNTS_MAPPING_CSV`).

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Snapshot | `data/processed/financials_<date>.parquet` | One row per company, latest 10-K values |
| Snapshot sample | `data/processed/financials_sample_max_1000_<date>.xlsx` | First 1000 rows of snapshot |
| Timeseries | `data/processed/financials_timeseries_<date>.xlsx` | One row per (company, period), 10-K and 10-Q |
| Timeseries delta | `data/processed/financials_timeseries_delta_<date>.xlsx` | Quarter-over-quarter deltas |
| Macro wide | `data/processed/macro_timeseries_wide_<date>.xlsx` | FRED series in wide format |
