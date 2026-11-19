"""Sequential benchmark orchestration."""

from __future__ import annotations

import math
import time

from bench_download.application.ports import HttpClient, HttpClientError
from bench_download.domain.models import BenchmarkResult, RequestSample


class RunBenchmarkUseCase:
    """Orchestrate requests through an injected port, not a concrete HTTP client."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def execute(
        self,
        url: str,
        *,
        count: int,
        connect_timeout: float,
        read_timeout: float,
        max_retries: int,
    ) -> BenchmarkResult:
        """Keep logical calls sequential while retaining individual failures."""
        if count < 1:
            raise ValueError("Request count must be at least one.")
        for name, value in (
            ("connect timeout", connect_timeout),
            ("read timeout", read_timeout),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name.capitalize()} must be finite and positive.")
        if max_retries < 0:
            raise ValueError("Maximum retries cannot be negative.")

        self._http_client.configure_retries(max_retries)
        samples: list[RequestSample] = []
        benchmark_started_at = time.perf_counter()

        for index in range(1, count + 1):
            request_started_at = time.perf_counter()
            try:
                bytes_downloaded = self._http_client.download(
                    url,
                    connect_timeout=connect_timeout,
                    read_timeout=read_timeout,
                )
            except HttpClientError as exc:
                samples.append(
                    RequestSample(
                        index=index,
                        latency_seconds=time.perf_counter() - request_started_at,
                        bytes_downloaded=0,
                        error=str(exc),
                    )
                )
            else:
                samples.append(
                    RequestSample(
                        index=index,
                        latency_seconds=time.perf_counter() - request_started_at,
                        bytes_downloaded=bytes_downloaded,
                    )
                )

        total_elapsed_seconds = time.perf_counter() - benchmark_started_at
        if total_elapsed_seconds <= 0:
            raise RuntimeError("Benchmark elapsed time must be positive.")
        return BenchmarkResult(
            url=url,
            requested_count=count,
            samples=tuple(samples),
            total_elapsed_seconds=total_elapsed_seconds,
        )
