"""Entrypoint for running the SEC financials pipeline."""

from __future__ import annotations

import logging

from src.config import (
    DEFAULT_MAX_COMPANIES,
    PROCESSED_FINANCIALS_PATH,
    PROCESSED_FINANCIALS_SAMPLE_PATH,
    SAMPLE_MAX_ROWS,
)
from src.edgar_client import fetch_ticker_universe
from src.pipeline import build_financials_dataframe
from src.utils import configure_logging, initialize_environment


def main() -> None:
    """Run the financials pipeline with a default ticker universe."""
    configure_logging()
    initialize_environment()

    max_companies = DEFAULT_MAX_COMPANIES
    tickers = fetch_ticker_universe()

    dataframe = build_financials_dataframe(tickers=tickers, max_companies=max_companies)

    logger = logging.getLogger(__name__)
    logger.info("Built financials dataframe with shape=%s", dataframe.shape)
    logger.info("Output persisted to %s", PROCESSED_FINANCIALS_PATH)
    logger.info(
        "Sample snapshot persisted to %s (max %d rows)",
        PROCESSED_FINANCIALS_SAMPLE_PATH,
        SAMPLE_MAX_ROWS,
    )


if __name__ == "__main__":
    main()
