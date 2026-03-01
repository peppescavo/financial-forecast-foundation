# Financial Forecast Foundation — Documentation

This folder documents the codebase for the Financial Forecast Foundation project: SEC EDGAR financial data and FRED macroeconomic pipelines.

## Contents

- **[Architecture](architecture.md)** — High-level design, data flow, and pipeline overview.
- **[Modules](modules.md)** — Reference for each Python module and main APIs.
- **[Configuration](configuration.md)** — Environment variables, macro accounts mapping, and paths.

## Quick links

- Project [README](../README.md) — Installation, run instructions, SEC/FRED setup.
- Entrypoint: `python main.py` (financials + macro).
- Discovery: `python scripts/discover_us_gaap_concepts.py` (us-gaap concept discovery and curation).
