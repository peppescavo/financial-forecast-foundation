"""Pipeline for building and persisting a modeling-ready financials DataFrame."""

from __future__ import annotations

import logging

import pandas as pd
from tqdm import tqdm

from src.config import (
    FINANCIAL_FIELDS,
    PROCESSED_FINANCIALS_PATH,
    PROCESSED_FINANCIALS_SAMPLE_PATH,
    SAMPLE_MAX_ROWS,
)
from src.financials import build_company_financials
from src.utils import ensure_directory

logger = logging.getLogger(__name__)


def build_financials_dataframe(tickers: list[str], max_companies: int) -> pd.DataFrame:
    """Build and persist a standardized financials DataFrame for input tickers."""
    selected_tickers = [ticker.strip().upper() for ticker in tickers[:max_companies]]

    records = [
        build_company_financials(ticker)
        for ticker in tqdm(
            selected_tickers,
            desc="Fetching SEC financials",
            unit="ticker",
        )
    ]

    if records:
        df = pd.DataFrame.from_records(records)
    else:
        df = pd.DataFrame(columns=["ticker", *FINANCIAL_FIELDS])

    df = df.set_index("ticker").reindex(selected_tickers)
    df = df.reindex(columns=FINANCIAL_FIELDS)
    df = df.apply(pd.to_numeric, errors="coerce")

    ensure_directory(PROCESSED_FINANCIALS_PATH.parent)
    df.to_parquet(PROCESSED_FINANCIALS_PATH, engine="pyarrow")
    df.head(SAMPLE_MAX_ROWS).to_excel(
        PROCESSED_FINANCIALS_SAMPLE_PATH,
        engine="openpyxl",
    )

    logger.info("Saved financials to %s", PROCESSED_FINANCIALS_PATH)
    logger.info(
        "Saved sample snapshot (max %d rows) to %s",
        SAMPLE_MAX_ROWS,
        PROCESSED_FINANCIALS_SAMPLE_PATH,
    )
    return df
