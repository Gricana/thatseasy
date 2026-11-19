"""Outbound interfaces required by application use cases."""

from __future__ import annotations

from typing import Protocol


class HttpClientError(Exception):
    """A request failed after the configured transport retries."""


class HttpClient(Protocol):
    """Structural port keeps orchestration independent of an HTTP library."""

    def configure_retries(self, max_retries: int) -> None:
        """Apply the retry policy for the upcoming sequential run."""

    def download(
        self, url: str, *, connect_timeout: float, read_timeout: float
    ) -> int:
        """Return bytes from a complete, non-empty response or raise an error."""
        ...
