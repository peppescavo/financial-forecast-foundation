"""Pipeline for building and persisting a modeling-ready financials DataFrame."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from src.config import (
    EFFECTIVE_REFERENCE_DATE_STR,
    FINANCIAL_FIELDS,
    PROCESSED_FINANCIALS_PATH,
    PROCESSED_FINANCIALS_SAMPLE_PATH,
    PROCESSED_FINANCIALS_TIMESERIES_PATH,
    PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH,
    SAMPLE_MAX_ROWS,
    SEC_FETCH_MAX_WORKERS,
    SUBMISSION_STATIC_FIELDS,
)
from src.edgar_client import normalize_cik
from src.financials import build_company_financials, build_company_financials_timeseries
from src.utils import ensure_directory

logger = logging.getLogger(__name__)


def build_financials_dataframe(
    ciks: list[str],
    max_companies: int,
    ticker_lookup: dict[str, str] | None = None,
    reference_date: str | None = None,
) -> pd.DataFrame:
    """Build and persist a standardized financials DataFrame for input CIKs."""
    cutoff = reference_date or EFFECTIVE_REFERENCE_DATE_STR
    selected_ciks = [normalize_cik(cik) for cik in ciks[:max_companies]]
    normalized_lookup = (
        {normalize_cik(cik): ticker for cik, ticker in ticker_lookup.items()}
        if ticker_lookup
        else {}
    )

    max_workers = SEC_FETCH_MAX_WORKERS
    records = [None] * len(selected_ciks)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(
                build_company_financials,
                cik,
                ticker=normalized_lookup.get(cik),
                reference_date=cutoff,
            ): i
            for i, cik in enumerate(selected_ciks)
        }
        for future in tqdm(
            as_completed(future_to_idx),
            total=len(future_to_idx),
            desc="Fetching SEC financials",
            unit="company",
        ):
            idx = future_to_idx[future]
            records[idx] = future.result()
    # Preserve order; failed companies still return a record (with NaN financials)
    assert all(r is not None for r in records), "unexpected missing record"

    if records:
        df = pd.DataFrame.from_records(records)
    else:
        df = pd.DataFrame(
            columns=[
                "cik",
                "ticker",
                "as_of_date",
                *SUBMISSION_STATIC_FIELDS,
                *FINANCIAL_FIELDS,
            ]
        )

    df = df.set_index("cik").reindex(selected_ciks)
    df = df.reindex(
        columns=[
            "ticker",
            "as_of_date",
            *SUBMISSION_STATIC_FIELDS,
            *FINANCIAL_FIELDS,
        ]
    )
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


def build_financials_timeseries_dataframe(
    ciks: list[str],
    max_companies: int,
    ticker_lookup: dict[str, str] | None = None,
    reference_date: str | None = None,
) -> pd.DataFrame:
    """Build and persist a long-format DataFrame: one row per (company, period)."""
    cutoff = reference_date or EFFECTIVE_REFERENCE_DATE_STR
    selected_ciks = [normalize_cik(cik) for cik in ciks[:max_companies]]
    normalized_lookup = (
        {normalize_cik(cik): ticker for cik, ticker in ticker_lookup.items()}
        if ticker_lookup
        else {}
    )

    max_workers = SEC_FETCH_MAX_WORKERS
    all_records: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cik = {
            executor.submit(
                build_company_financials_timeseries,
                cik,
                ticker=normalized_lookup.get(cik),
                reference_date=cutoff,
            ): cik
            for cik in selected_ciks
        }
        for future in tqdm(
            as_completed(future_to_cik),
            total=len(future_to_cik),
            desc="Fetching SEC financials (timeseries)",
            unit="company",
        ):
            records = future.result()
            all_records.extend(records)

    if not all_records:
        df = pd.DataFrame(
            columns=[
                "cik",
                "ticker",
                "as_of_date",
                *SUBMISSION_STATIC_FIELDS,
                *FINANCIAL_FIELDS,
            ]
        )
    else:
        df = pd.DataFrame.from_records(all_records)
        df = df.reindex(
            columns=[
                "cik",
                "ticker",
                "as_of_date",
                *SUBMISSION_STATIC_FIELDS,
                *FINANCIAL_FIELDS,
            ]
        )

    df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
    df[FINANCIAL_FIELDS] = df[FINANCIAL_FIELDS].apply(pd.to_numeric, errors="coerce")

    ensure_directory(PROCESSED_FINANCIALS_TIMESERIES_PATH.parent)
    df.to_excel(
        PROCESSED_FINANCIALS_TIMESERIES_PATH,
        engine="openpyxl",
        index=False,
        sheet_name="timeseries",
    )

    logger.info(
        "Saved financials timeseries (shape=%s) to %s",
        df.shape,
        PROCESSED_FINANCIALS_TIMESERIES_PATH,
    )
    return df


def build_financials_timeseries_delta_dataframe(
    timeseries_df: pd.DataFrame,
    *,
    tolerance_days: int = 20,
) -> pd.DataFrame:
    """Build a delta DataFrame from a (company, period) financials time series.

    The delta dataset contains one row per pair of consecutive quarterly period ends
    (no gaps). Financial values are computed as (current - previous).
    """
    output_columns = [
        "cik",
        "ticker",
        "as_of_date",
        "as_of_date_prev",
        *SUBMISSION_STATIC_FIELDS,
        *FINANCIAL_FIELDS,
    ]
    if timeseries_df.empty:
        return pd.DataFrame(columns=output_columns)

    df = timeseries_df.copy()
    df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
    df = df.dropna(subset=["cik", "as_of_date"]).copy()
    if df.empty:
        return pd.DataFrame(columns=output_columns)

    df = df.sort_values(["cik", "as_of_date"], kind="stable").reset_index(drop=True)
    grouped = df.groupby("cik", sort=False)
    prev_dates = grouped["as_of_date"].shift(1)

    expected_current_dates = prev_dates + pd.DateOffset(months=3)
    gap_days = (df["as_of_date"] - prev_dates).dt.days
    is_prev_quarter = (
        prev_dates.notna()
        & (df["as_of_date"] > prev_dates)
        & (df["as_of_date"] - expected_current_dates).abs().dt.days.le(tolerance_days)
        & gap_days.between(70, 110)
    )

    prev_values = grouped[FINANCIAL_FIELDS].shift(1)
    delta_values = df[FINANCIAL_FIELDS] - prev_values

    delta_df = df.loc[
        is_prev_quarter, ["cik", "ticker", "as_of_date", *SUBMISSION_STATIC_FIELDS]
    ].copy()
    delta_df["as_of_date_prev"] = prev_dates.loc[is_prev_quarter].to_numpy()
    delta_df[FINANCIAL_FIELDS] = delta_values.loc[
        is_prev_quarter, FINANCIAL_FIELDS
    ].to_numpy()
    delta_df["as_of_date_prev"] = pd.to_datetime(
        delta_df["as_of_date_prev"], errors="coerce"
    )
    delta_df[FINANCIAL_FIELDS] = delta_df[FINANCIAL_FIELDS].apply(
        pd.to_numeric, errors="coerce"
    )
    delta_df = delta_df.reindex(columns=output_columns)
    return delta_df


def persist_financials_timeseries_delta_dataframe(delta_df: pd.DataFrame) -> None:
    ensure_directory(PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH.parent)
    delta_df.to_excel(
        PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH,
        engine="openpyxl",
        index=False,
        sheet_name="delta",
    )
    logger.info(
        "Saved financials timeseries delta (shape=%s) to %s",
        delta_df.shape,
        PROCESSED_FINANCIALS_TIMESERIES_DELTA_PATH,
    )
