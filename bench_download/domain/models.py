"""Immutable benchmark values and derived domain metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

from bench_download.domain.statistics import (
    LatencyStatistics,
    calculate_latency_statistics,
)

BYTES_PER_MIB = 1024 * 1024
BYTES_PER_MB = 1_000_000


@dataclass(frozen=True, slots=True)
class RequestSample:
    """One logical request, including its final outcome after transport retries."""

    index: int
    latency_seconds: float
    bytes_downloaded: int
    error: str | None = None

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("Request index must be positive.")
        if not math.isfinite(self.latency_seconds) or self.latency_seconds < 0:
            raise ValueError("Request latency must be finite and non-negative.")
        if self.bytes_downloaded < 0:
            raise ValueError("Downloaded bytes cannot be negative.")
        if self.error is not None and self.bytes_downloaded != 0:
            raise ValueError("Failed requests cannot contribute downloaded bytes.")

    @property
    def succeeded(self) -> bool:
        """Whether the complete response was accepted."""
        return self.error is None


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """A complete run; failed samples remain visible instead of aborting the run."""

    url: str
    requested_count: int
    samples: tuple[RequestSample, ...]
    total_elapsed_seconds: float

    def __post_init__(self) -> None:
        if self.requested_count < 1 or len(self.samples) != self.requested_count:
            raise ValueError("The result must contain one sample per requested call.")
        if any(sample.index != index for index, sample in enumerate(self.samples, 1)):
            raise ValueError("Request samples must be consecutively indexed from one.")
        if (
            not math.isfinite(self.total_elapsed_seconds)
            or self.total_elapsed_seconds <= 0
        ):
            raise ValueError("Total elapsed time must be finite and positive.")

    @property
    def successful_count(self) -> int:
        """Number of complete successful downloads."""
        return sum(sample.succeeded for sample in self.samples)

    @property
    def failed_count(self) -> int:
        """Number of failed logical requests."""
        return self.requested_count - self.successful_count

    @property
    def total_bytes(self) -> int:
        """Bytes from successful, fully consumed response bodies."""
        return sum(sample.bytes_downloaded for sample in self.samples)

    @property
    def total_megabytes(self) -> float:
        """Decimal megabytes from successful, fully consumed response bodies."""
        return self.total_bytes / BYTES_PER_MB

    @property
    def throughput_mib_per_second(self) -> float:
        """Aggregate successful payload bytes per wall-clock second."""
        return self.total_bytes / BYTES_PER_MIB / self.total_elapsed_seconds

    @property
    def cold_latency(self) -> LatencyStatistics:
        """Latency statistics for the first logical request."""
        return calculate_latency_statistics((self.samples[0].latency_seconds,))

    @property
    def warm_latency(self) -> LatencyStatistics:
        """Latency statistics for all logical requests after the first."""
        return calculate_latency_statistics(
            sample.latency_seconds for sample in self.samples[1:]
        )
