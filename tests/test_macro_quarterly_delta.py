"""Unit tests for macro quarterly resampling and delta construction."""

from __future__ import annotations

import pandas as pd

from src.macro_pipeline import (
    build_macro_timeseries_quarterly_delta_dataframe,
    build_macro_timeseries_quarterly_wide_dataframe,
)


def test_build_macro_timeseries_quarterly_wide_dataframe_resample_qe_last() -> None:
    wide_df = pd.DataFrame(
        {
            "GDPC1": [1.0, 2.0, 5.0, 6.0],
            "UNRATE": [4.0, 4.1, 4.2, 4.3],
        },
        index=pd.to_datetime(
            ["2025-01-10", "2025-03-15", "2025-06-29", "2025-06-30"], errors="coerce"
        ),
    )
    wide_df.index.name = "date"

    quarterly_df = build_macro_timeseries_quarterly_wide_dataframe(wide_df)

    assert list(quarterly_df.index) == [
        pd.Timestamp("2025-03-31"),
        pd.Timestamp("2025-06-30"),
    ]
    assert quarterly_df.loc[pd.Timestamp("2025-03-31"), "GDPC1"] == 2.0
    assert quarterly_df.loc[pd.Timestamp("2025-06-30"), "GDPC1"] == 6.0


def test_build_macro_timeseries_quarterly_wide_dataframe_resample_qe_mean() -> None:
    wide_df = pd.DataFrame(
        {"GDPC1": [1.0, 3.0, 5.0, 7.0]},
        index=pd.to_datetime(
            ["2025-01-10", "2025-03-15", "2025-04-01", "2025-06-30"], errors="coerce"
        ),
    )
    wide_df.index.name = "date"

    quarterly_df = build_macro_timeseries_quarterly_wide_dataframe(wide_df, agg="mean")

    assert list(quarterly_df.index) == [
        pd.Timestamp("2025-03-31"),
        pd.Timestamp("2025-06-30"),
    ]
    assert quarterly_df.loc[pd.Timestamp("2025-03-31"), "GDPC1"] == 2.0
    assert quarterly_df.loc[pd.Timestamp("2025-06-30"), "GDPC1"] == 6.0


def test_build_macro_timeseries_quarterly_delta_dataframe_pct_change() -> None:
    quarterly_wide_df = pd.DataFrame(
        {"GDPC1": [2.0, 6.0], "UNRATE": [4.1, 4.3]},
        index=pd.to_datetime(["2025-03-31", "2025-06-30"], errors="coerce"),
    )
    quarterly_wide_df.index.name = "date"

    delta_df = build_macro_timeseries_quarterly_delta_dataframe(quarterly_wide_df)

    assert pd.isna(delta_df.loc[pd.Timestamp("2025-03-31"), "GDPC1"])
    assert (
        delta_df.loc[pd.Timestamp("2025-06-30"), "GDPC1"] == ((6.0 - 2.0) / 2.0) * 100.0
    )
    assert (
        delta_df.loc[pd.Timestamp("2025-06-30"), "UNRATE"]
        == ((4.3 - 4.1) / 4.1) * 100.0
    )
