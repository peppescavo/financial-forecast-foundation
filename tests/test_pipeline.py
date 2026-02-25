"""Integration-style tests for the financials pipeline."""

from __future__ import annotations

import pandas as pd

from src.config import FINANCIAL_FIELDS, PROCESSED_FINANCIALS_SAMPLE_PATH
from src.pipeline import build_financials_dataframe
from src.utils import initialize_environment


def test_build_financials_dataframe_two_tickers() -> None:
    """Pipeline should return a DataFrame with expected index and columns."""
    initialize_environment()
    tickers = ["AAPL", "MSFT"]

    df = build_financials_dataframe(tickers=tickers, max_companies=2)

    assert isinstance(df, pd.DataFrame)
    assert all(column in df.columns for column in FINANCIAL_FIELDS)
    assert df.index.tolist() == tickers
    assert PROCESSED_FINANCIALS_SAMPLE_PATH.exists()
