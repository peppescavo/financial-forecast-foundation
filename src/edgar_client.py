"""SEC EDGAR API client utilities."""

from __future__ import annotations

import threading
import time
from collections import deque
from functools import lru_cache

import requests

from src import config

_lock = threading.Lock()
_request_times: deque[float] = deque()


def _format_cik(cik: str) -> str:
    """Normalize CIK to a 10-digit zero-padded string."""
    digits = "".join(char for char in cik if char.isdigit())
    if not digits:
        raise ValueError(f"Invalid CIK: {cik}")
    return digits.zfill(10)


def _sec_get(url: str) -> dict:
    """Perform a rate-limited GET request against SEC endpoints (thread-safe)."""
    max_rps = getattr(config, "SEC_MAX_REQUESTS_PER_SECOND", 10)
    with _lock:
        now = time.monotonic()
        while _request_times and _request_times[0] < now - 1.0:
            _request_times.popleft()
        while len(_request_times) >= max_rps:
            # wait until oldest request is older than 1 second
            sleep_for = 1.0 - (now - _request_times[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            while _request_times and _request_times[0] < now - 1.0:
                _request_times.popleft()
        _request_times.append(time.monotonic())

    response = requests.get(
        url,
        headers=config.SEC_HEADERS,
        timeout=config.SEC_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


@lru_cache(maxsize=1)
def _ticker_map() -> dict[str, str]:
    """Fetch and cache ticker-to-CIK mappings from SEC."""
    payload = _sec_get(config.SEC_TICKER_MAPPING_URL)
    return {
        item["ticker"].upper(): f"{int(item['cik_str']):010d}"
        for item in payload.values()
    }


def ticker_to_cik(ticker: str) -> str:
    """Resolve ticker to a zero-padded CIK string."""
    normalized = ticker.strip().upper()
    cik = _ticker_map().get(normalized)
    if cik is None:
        raise ValueError(f"Ticker not found: {ticker}")
    return cik


def normalize_cik(cik: str) -> str:
    """Normalize a raw CIK value into the SEC 10-digit format."""
    return _format_cik(cik)


def fetch_cik_universe_with_tickers() -> list[tuple[str, str]]:
    """Fetch unique CIKs with one representative ticker per company."""
    cik_to_ticker: dict[str, str] = {}
    for ticker, cik in _ticker_map().items():
        cik_to_ticker.setdefault(cik, ticker)
    return sorted(cik_to_ticker.items(), key=lambda item: item[0])


def fetch_company_submissions(cik: str) -> dict:
    """Fetch company submissions JSON (metadata: industry, location, etc.) for the provided CIK."""
    cik_padded = _format_cik(cik)
    url = config.SEC_SUBMISSIONS_URL.format(cik=cik_padded)
    return _sec_get(url)


def fetch_company_submissions_and_facts(cik: str) -> tuple[dict, dict]:
    """Fetch both submissions (metadata) and company facts (XBRL) for the provided CIK. Two requests."""
    submissions = fetch_company_submissions(cik)
    cik_padded = _format_cik(cik)
    company_facts_url = config.SEC_COMPANY_FACTS_URL.format(cik=cik_padded)
    facts = _sec_get(company_facts_url)
    return submissions, facts


def fetch_company_facts(cik: str) -> dict:
    """Fetch company XBRL facts JSON for the provided CIK."""
    _, facts = fetch_company_submissions_and_facts(cik)
    return facts
