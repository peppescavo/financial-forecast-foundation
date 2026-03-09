"""Unit tests for timeseries delta construction."""

from __future__ import annotations

import pandas as pd

from src.config import FINANCIAL_FIELDS
from src.pipeline import build_financials_timeseries_delta_dataframe


def test_build_financials_timeseries_delta_dataframe_requires_consecutive_quarters() -> (
    None
):
    rows = []
    for cik, dates, base in [
        ("0000000001", ["2025-03-31", "2025-06-30", "2025-12-31"], 10.0),
        ("0000000002", ["2025-03-30", "2025-06-29"], 100.0),
    ]:
        for i, date in enumerate(dates):
            row = {
                "cik": cik,
                "ticker": "TST",
                "as_of_date": date,
                "company_name": "Test Co",
                "industry": "Test",
                "region": "US",
            }
            for field in FINANCIAL_FIELDS:
                row[field] = base + i
            rows.append(row)

    ts_df = pd.DataFrame.from_records(rows)
    ts_df["as_of_date"] = pd.to_datetime(ts_df["as_of_date"], errors="coerce")

    delta_df = build_financials_timeseries_delta_dataframe(ts_df, tolerance_days=20)

    assert "as_of_date_prev" in delta_df.columns
    assert set(delta_df["cik"].unique()) == {"0000000001", "0000000002"}

    # cik=1: only 2025-06-30 qualifies (prev=2025-03-31; gap after that).
    cik1 = delta_df[delta_df["cik"] == "0000000001"].sort_values("as_of_date")
    assert len(cik1) == 1
    assert cik1.iloc[0]["as_of_date"] == pd.Timestamp("2025-06-30")
    assert cik1.iloc[0]["as_of_date_prev"] == pd.Timestamp("2025-03-31")
    assert cik1.iloc[0][FINANCIAL_FIELDS[0]] == (11.0 - 10.0) / 10.0

    # cik=2: fiscal-ish quarter ends still qualify within tolerance.
    cik2 = delta_df[delta_df["cik"] == "0000000002"].sort_values("as_of_date")
    assert len(cik2) == 1
    assert cik2.iloc[0]["as_of_date"] == pd.Timestamp("2025-06-29")
    assert cik2.iloc[0]["as_of_date_prev"] == pd.Timestamp("2025-03-30")
    assert cik2.iloc[0][FINANCIAL_FIELDS[0]] == (101.0 - 100.0) / 100.0
