"""Pipeline for downloading and persisting macroeconomic time series from FRED."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from src import config
from src.fred_client import fetch_series_observations
from src.utils import ensure_directory

logger = logging.getLogger(__name__)


def _empty_long_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=["series_id", "series_name", "date", "value"])


def _observations_payload_to_frame(series_id: str, payload: dict) -> pd.DataFrame:
    observations = payload.get("observations") or []
    if not observations:
        return pd.DataFrame(
            {
                "series_id": pd.Series(dtype="string"),
                "series_name": pd.Series(dtype="string"),
                "date": pd.Series(dtype="datetime64[ns]"),
                "value": pd.Series(dtype="float64"),
            }
        )

    df = pd.DataFrame.from_records(observations)
    if not {"date", "value"}.issubset(df.columns):
        return _empty_long_dataframe()

    df = df[["date", "value"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    df["series_name"] = config.FRED_DEFAULT_SERIES.get(series_id, "")
    df = df.dropna(subset=["date"])
    return df


def build_macro_timeseries_long_dataframe(
    series_ids: list[str] | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
) -> pd.DataFrame:
    """Build a long-format macro DataFrame: one row per (series_id, date)."""
    if not config.FRED_API_KEY:
        logger.warning(
            "FRED_API_KEY is not set; skipping macro download. Add it to `.env` as FRED_API_KEY=..."
        )
        return _empty_long_dataframe()

    selected_series_ids = series_ids or list(config.FRED_DEFAULT_SERIES.keys())
    start = observation_start or config.FRED_OBSERVATION_START
    end = (
        observation_end if observation_end is not None else config.FRED_OBSERVATION_END
    )
    end = end or None

    frames: list[pd.DataFrame] = []
    max_workers = config.FRED_FETCH_MAX_WORKERS
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_series = {
            executor.submit(
                fetch_series_observations,
                series_id,
                observation_start=start,
                observation_end=end,
            ): series_id
            for series_id in selected_series_ids
        }
        for future in tqdm(
            as_completed(future_to_series),
            total=len(future_to_series),
            desc="Fetching FRED macro series",
            unit="series",
        ):
            series_id = future_to_series[future]
            try:
                payload = future.result()
            except Exception:
                logger.exception("Failed to fetch FRED series_id=%s", series_id)
                continue
            frames.append(_observations_payload_to_frame(series_id, payload))

    if not frames:
        return _empty_long_dataframe()

    df = pd.concat(frames, ignore_index=True)
    df = df.reindex(columns=["series_id", "series_name", "date", "value"])
    df = df.sort_values(["series_id", "date"], kind="stable").reset_index(drop=True)
    return df


def build_macro_timeseries_wide_dataframe(long_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long macro series into a wide DataFrame: one row per date, one col per series_id."""
    if long_df.empty:
        return pd.DataFrame()

    wide_df = long_df.pivot_table(
        index="date",
        columns="series_id",
        values="value",
        aggfunc="last",
    ).sort_index()
    wide_df.columns.name = None
    return wide_df


def build_and_persist_macro_timeseries(
    series_ids: list[str] | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download macro series from FRED and persist both long and wide Excel outputs."""
    long_df = build_macro_timeseries_long_dataframe(
        series_ids=series_ids,
        observation_start=observation_start,
        observation_end=observation_end,
    )
    wide_df = build_macro_timeseries_wide_dataframe(long_df)

    if long_df.empty:
        return long_df, wide_df

    ensure_directory(config.PROCESSED_MACRO_LONG_PATH.parent)
    long_df.to_excel(
        config.PROCESSED_MACRO_LONG_PATH,
        engine="openpyxl",
        index=False,
    )
    wide_df.reset_index().to_excel(
        config.PROCESSED_MACRO_WIDE_PATH,
        engine="openpyxl",
        index=False,
    )

    logger.info("Saved macro long to %s", config.PROCESSED_MACRO_LONG_PATH)
    logger.info("Saved macro wide to %s", config.PROCESSED_MACRO_WIDE_PATH)
    return long_df, wide_df
