"""Entrypoint for running the SEC financials pipeline + FRED macro download."""

from __future__ import annotations

import logging

from src.config import (
    DEFAULT_MAX_COMPANIES,
    PROCESSED_FINANCIALS_PATH,
    PROCESSED_FINANCIALS_SAMPLE_PATH,
    PROCESSED_FINANCIALS_TIMESERIES_PATH,
    PROCESSED_MACRO_LONG_PATH,
    PROCESSED_MACRO_WIDE_PATH,
    SAMPLE_MAX_ROWS,
)
from src.edgar_client import fetch_cik_universe_with_tickers
from src.macro_pipeline import build_and_persist_macro_timeseries
from src.pipeline import (
    build_financials_dataframe,
    build_financials_timeseries_dataframe,
)
from src.utils import configure_logging, initialize_environment


def main() -> None:
    """Run the financials pipeline with a default CIK universe."""
    configure_logging()
    initialize_environment()

    logger = logging.getLogger(__name__)
    max_companies = DEFAULT_MAX_COMPANIES
    companies = fetch_cik_universe_with_tickers()
    ciks = [cik for cik, _ in companies]
    ticker_lookup = {cik: ticker for cik, ticker in companies}

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

    ts_dataframe = build_financials_timeseries_dataframe(
        ciks=ciks,
        max_companies=max_companies,
        ticker_lookup=ticker_lookup,
    )
    logger.info("Built financials timeseries with shape=%s", ts_dataframe.shape)
    logger.info("Timeseries persisted to %s", PROCESSED_FINANCIALS_TIMESERIES_PATH)

    macro_long_df, _macro_wide_df = build_and_persist_macro_timeseries()
    if not macro_long_df.empty:
        logger.info("Built macro long dataframe with shape=%s", macro_long_df.shape)
        logger.info("Macro long persisted to %s", PROCESSED_MACRO_LONG_PATH)
        logger.info("Macro wide persisted to %s", PROCESSED_MACRO_WIDE_PATH)


if __name__ == "__main__":
    main()
