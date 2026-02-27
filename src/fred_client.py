"""FRED API client utilities."""

from __future__ import annotations

import threading
import time
from collections import deque

import requests

from src import config

_lock = threading.Lock()
_request_times: deque[float] = deque()


def _fred_get(url: str, params: dict[str, str]) -> dict:
    """Perform a rate-limited GET request against FRED endpoints (thread-safe)."""
    api_key = getattr(config, "FRED_API_KEY", "") or ""
    if not api_key:
        raise ValueError(
            "FRED_API_KEY is not set. Create a `.env` file with FRED_API_KEY=... "
            "or set it in the environment before running."
        )

    max_rps = getattr(config, "FRED_MAX_REQUESTS_PER_SECOND", 5)
    with _lock:
        now = time.monotonic()
        while _request_times and _request_times[0] < now - 1.0:
            _request_times.popleft()
        while len(_request_times) >= max_rps:
            sleep_for = 1.0 - (now - _request_times[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            while _request_times and _request_times[0] < now - 1.0:
                _request_times.popleft()
        _request_times.append(time.monotonic())

    final_params = {
        **params,
        "api_key": api_key,
        "file_type": "json",
    }

    response = requests.get(
        url,
        params=final_params,
        timeout=getattr(config, "FRED_TIMEOUT_SECONDS", 30),
    )
    response.raise_for_status()
    return response.json()


def fetch_series_observations(
    series_id: str,
    observation_start: str | None = None,
    observation_end: str | None = None,
) -> dict:
    """Fetch FRED observations for a series."""
    params: dict[str, str] = {"series_id": series_id}
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
    return _fred_get(config.FRED_SERIES_OBSERVATIONS_URL, params=params)


def fetch_series_metadata(series_id: str) -> dict:
    """Fetch FRED series metadata (title, units, frequency, etc.)."""
    return _fred_get(config.FRED_SERIES_URL, params={"series_id": series_id})
