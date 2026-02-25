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
from src.edgar_client import normalize_cik
from src.financials import build_company_financials
from src.utils import ensure_directory

logger = logging.getLogger(__name__)


def build_financials_dataframe(
    ciks: list[str],
    max_companies: int,
    ticker_lookup: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Build and persist a standardized financials DataFrame for input CIKs."""
    selected_ciks = [normalize_cik(cik) for cik in ciks[:max_companies]]
    normalized_lookup = (
        {normalize_cik(cik): ticker for cik, ticker in ticker_lookup.items()}
        if ticker_lookup
        else {}
    )

    records = [
        build_company_financials(cik, ticker=normalized_lookup.get(cik))
        for cik in tqdm(
            selected_ciks,
            desc="Fetching SEC financials",
            unit="company",
        )
    ]

    if records:
        df = pd.DataFrame.from_records(records)
    else:
        df = pd.DataFrame(columns=["cik", "ticker", "as_of_date", *FINANCIAL_FIELDS])

    df = df.set_index("cik").reindex(selected_ciks)
    df = df.reindex(columns=["ticker", "as_of_date", *FINANCIAL_FIELDS])
    df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
    df[FINANCIAL_FIELDS] = df[FINANCIAL_FIELDS].apply(pd.to_numeric, errors="coerce")

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
