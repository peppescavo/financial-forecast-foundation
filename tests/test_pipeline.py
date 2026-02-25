"""Integration-style tests for the financials pipeline."""

from __future__ import annotations

import pandas as pd

from src.config import FINANCIAL_FIELDS, PROCESSED_FINANCIALS_SAMPLE_PATH
from src.pipeline import build_financials_dataframe
from src.utils import initialize_environment


def test_build_financials_dataframe_two_companies() -> None:
    """Pipeline should return a DataFrame with expected CIK index and columns."""
    initialize_environment()
    ciks = ["0000320193", "0000789019"]
    ticker_lookup = {
        "0000320193": "AAPL",
        "0000789019": "MSFT",
    }

    df = build_financials_dataframe(
        ciks=ciks,
        max_companies=2,
        ticker_lookup=ticker_lookup,
    )

    assert isinstance(df, pd.DataFrame)
    assert all(column in df.columns for column in FINANCIAL_FIELDS)
    assert "as_of_date" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["as_of_date"])
    assert df.index.tolist() == ciks
    assert "ticker" in df.columns
    assert df["ticker"].tolist() == ["AAPL", "MSFT"]
    assert PROCESSED_FINANCIALS_SAMPLE_PATH.exists()
