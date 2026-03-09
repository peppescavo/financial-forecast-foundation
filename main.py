"""Entrypoint for running the SEC financials pipeline + FRED macro download."""

from __future__ import annotations

import logging
import os

import pandas as pd

from src.config import (
    DEFAULT_MAX_COMPANIES,
    EFFECTIVE_REFERENCE_DATE_STR,
    PROCESSED_FINANCIALS_PATH,
    PROCESSED_FINANCIALS_SAMPLE_PATH,
    PROCESSED_FINANCIALS_TIMESERIES_PATH,
    PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH,
    PROCESSED_MACRO_WIDE_PATH,
    PROCESSED_MACRO_QUARTERLY_WIDE_PATH,
    PROCESSED_MACRO_QUARTERLY_DELTA_PATH,
    PROCESSED_MACRO_QUARTERLY_WIDE_MEAN_PATH,
    PROCESSED_MACRO_QUARTERLY_DELTA_MEAN_PATH,
    SAMPLE_MAX_ROWS,
)
from src.edgar_client import fetch_cik_universe_with_tickers
from src.macro_pipeline import build_and_persist_macro_timeseries
from src.pipeline import (
    build_financials_dataframe,
    build_financials_timeseries_delta_dataframe,
    build_financials_timeseries_dataframe,
    persist_financials_timeseries_delta_dataframe,
)
from src.utils import configure_logging, initialize_environment


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y"}


def main() -> None:
    """Run the financials pipeline with a default CIK universe."""
    configure_logging()
    initialize_environment()

    logger = logging.getLogger(__name__)
    logger.info("Using reference date cutoff=%s", EFFECTIVE_REFERENCE_DATE_STR)
    refresh_financials = _truthy_env("REFRESH_FINANCIALS")
    needs_snapshot = refresh_financials or not PROCESSED_FINANCIALS_PATH.exists()
    needs_timeseries = (
        refresh_financials or not PROCESSED_FINANCIALS_TIMESERIES_PATH.exists()
    )

    ts_dataframe: pd.DataFrame | None = None
    if needs_snapshot or needs_timeseries:
        max_companies = DEFAULT_MAX_COMPANIES
        companies = fetch_cik_universe_with_tickers()
        ciks = [cik for cik, _ in companies]
        ticker_lookup = {cik: ticker for cik, ticker in companies}

        if needs_snapshot:
            dataframe = build_financials_dataframe(
                ciks=ciks,
                max_companies=max_companies,
                ticker_lookup=ticker_lookup,
            )
            logger.info("Built financials dataframe with shape=%s", dataframe.shape)
            logger.info("Output persisted to %s", PROCESSED_FINANCIALS_PATH)
            logger.info(
                "Sample snapshot persisted to %s (max %d rows)",
                PROCESSED_FINANCIALS_SAMPLE_PATH,
                SAMPLE_MAX_ROWS,
            )
        else:
            logger.info(
                "Financials snapshot already exists at %s; skipping SEC download (set REFRESH_FINANCIALS=1 to rebuild).",
                PROCESSED_FINANCIALS_PATH,
            )

        if needs_timeseries:
            ts_dataframe = build_financials_timeseries_dataframe(
                ciks=ciks,
                max_companies=max_companies,
                ticker_lookup=ticker_lookup,
            )
            logger.info("Built financials timeseries with shape=%s", ts_dataframe.shape)
            logger.info(
                "Timeseries persisted to %s", PROCESSED_FINANCIALS_TIMESERIES_PATH
            )
        else:
            logger.info(
                "Financials timeseries already exists at %s; skipping SEC download (set REFRESH_FINANCIALS=1 to rebuild).",
                PROCESSED_FINANCIALS_TIMESERIES_PATH,
            )
    else:
        logger.info(
            "Financials outputs already exist; skipping SEC download (set REFRESH_FINANCIALS=1 to rebuild)."
        )

    if ts_dataframe is None:
        if not PROCESSED_FINANCIALS_TIMESERIES_PATH.exists():
            logger.warning(
                "Timeseries file not found at %s; skipping delta build.",
                PROCESSED_FINANCIALS_TIMESERIES_PATH,
            )
        else:
            logger.info(
                "Loading existing timeseries from %s to build delta.",
                PROCESSED_FINANCIALS_TIMESERIES_PATH,
            )
            ts_dataframe = pd.read_excel(
                PROCESSED_FINANCIALS_TIMESERIES_PATH,
                sheet_name="timeseries",
            )

    if ts_dataframe is not None:
        delta_df = build_financials_timeseries_delta_dataframe(ts_dataframe)
        persist_financials_timeseries_delta_dataframe(delta_df)
        logger.info(
            "Timeseries delta persisted to %s",
            PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH,
        )

    _macro_long_df, macro_wide_df = build_and_persist_macro_timeseries()
    if not macro_wide_df.empty:
        logger.info("Built macro wide dataframe with shape=%s", macro_wide_df.shape)
        logger.info("Macro wide persisted to %s", PROCESSED_MACRO_WIDE_PATH)
        if PROCESSED_MACRO_QUARTERLY_WIDE_PATH.exists():
            logger.info(
                "Macro quarterly wide persisted to %s",
                PROCESSED_MACRO_QUARTERLY_WIDE_PATH,
            )
        if PROCESSED_MACRO_QUARTERLY_DELTA_PATH.exists():
            logger.info(
                "Macro quarterly delta persisted to %s",
                PROCESSED_MACRO_QUARTERLY_DELTA_PATH,
            )
        if PROCESSED_MACRO_QUARTERLY_WIDE_MEAN_PATH.exists():
            logger.info(
                "Macro quarterly wide mean persisted to %s",
                PROCESSED_MACRO_QUARTERLY_WIDE_MEAN_PATH,
            )
        if PROCESSED_MACRO_QUARTERLY_DELTA_MEAN_PATH.exists():
            logger.info(
                "Macro quarterly delta mean persisted to %s",
                PROCESSED_MACRO_QUARTERLY_DELTA_MEAN_PATH,
            )


if __name__ == "__main__":
    main()
