"""Requests-based streaming HTTP adapter with connection pooling and retries."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bench_download.application.ports import HttpClient, HttpClientError
from bench_download.config import (
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_USER_AGENT,
    DOWNLOAD_CHUNK_SIZE,
    RETRYABLE_STATUS_CODES,
)


class RequestsHttpClient(HttpClient):
    """Reuse a Session so sequential requests can reuse pooled connections."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        session: requests.Session | None = None,
    ) -> None:
        self._session = session if session is not None else requests.Session()
        self._session.headers["User-Agent"] = user_agent
        self._max_retries: int | None = None

    def __enter__(self) -> RequestsHttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def configure_retries(self, max_retries: int) -> None:
        """Mount retry-aware adapters once per changed run policy."""
        if max_retries < 0:
            raise ValueError("Maximum retries cannot be negative.")
        if max_retries == self._max_retries:
            return

        retry = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=DEFAULT_RETRY_BACKOFF_SECONDS,
            status_forcelist=RETRYABLE_STATUS_CODES,
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        self._session.mount("http://", HTTPAdapter(max_retries=retry))
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._max_retries = max_retries

    def download(
        self, url: str, *, connect_timeout: float, read_timeout: float
    ) -> int:
        """Stream a body to count bytes without retaining it in memory."""
        if self._max_retries is None:
            self.configure_retries(0)
        try:
            with self._session.get(
                url,
                timeout=(connect_timeout, read_timeout),
                stream=True,
            ) as response:
                response.raise_for_status()
                downloaded_bytes = sum(
                    len(chunk)
                    for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE)
                    if chunk
                )
                if downloaded_bytes == 0:
                    raise HttpClientError("Response body is empty.")
                return downloaded_bytes
        except requests.RequestException as exc:
            if isinstance(exc, requests.HTTPError) and exc.response is not None:
                detail = f"HTTP {exc.response.status_code}"
            else:
                detail = f"Network error ({type(exc).__name__})"
            raise HttpClientError(detail) from exc

    def close(self) -> None:
        """Close the pooled connections owned by this adapter."""
        self._session.close()
