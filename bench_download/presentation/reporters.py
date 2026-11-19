"""Text and JSON renderers with no transport-library dependencies."""

from __future__ import annotations

import json
from urllib.parse import urlsplit

from bench_download.domain.models import BenchmarkResult, RequestSample
from bench_download.domain.statistics import LatencyStatistics


def _safe_target(url: str) -> str:
    """Show only authority, avoiding credentials, paths, and query tokens in logs."""
    parsed = urlsplit(url)
    hostname = parsed.hostname or ""
    if ":" in hostname:
        hostname = f"[{hostname}]"
    if parsed.port is not None:
        hostname = f"{hostname}:{parsed.port}"
    return hostname


def _latency_payload(stats: LatencyStatistics) -> dict[str, int | float | None]:
    return {
        "count": stats.count,
        "min_seconds": stats.minimum_seconds,
        "median_seconds": stats.median_seconds,
        "mean_seconds": stats.mean_seconds,
        "stdev_seconds": stats.stdev_seconds,
        "p95_seconds": stats.p95_seconds,
    }


def _sample_payload(sample: RequestSample) -> dict[str, int | float | str | bool | None]:
    return {
        "index": sample.index,
        "phase": "cold" if sample.index == 1 else "warm",
        "latency_seconds": sample.latency_seconds,
        "bytes_downloaded": sample.bytes_downloaded,
        "success": sample.succeeded,
        "error": sample.error,
    }


class JsonReporter:
    """Render a stable JSON shape suitable for CI and monitoring."""

    def render(self, result: BenchmarkResult) -> str:
        """Return JSON with metrics and per-request outcomes."""
        payload = {
            "target": _safe_target(result.url),
            "requested_requests": result.requested_count,
            "successful_requests": result.successful_count,
            "failed_requests": result.failed_count,
            "total_bytes": result.total_bytes,
            "total_megabytes": result.total_megabytes,
            "total_elapsed_seconds": result.total_elapsed_seconds,
            "throughput_mib_per_second": result.throughput_mib_per_second,
            "latency": {
                "cold": _latency_payload(result.cold_latency),
                "warm": _latency_payload(result.warm_latency),
            },
            "requests": [_sample_payload(sample) for sample in result.samples],
        }
        return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)


class TextReporter:
    """Render a concise human-readable benchmark summary."""

    def render(self, result: BenchmarkResult) -> str:
        """Return text summary and individual failure details."""
        lines = [
            f"Target: {_safe_target(result.url)}",
            (
                f"Requests: {result.successful_count}/{result.requested_count} "
                f"successful ({result.failed_count} failed)"
            ),
            (
                f"Downloaded: {result.total_megabytes:.3f} MB "
                f"({result.total_bytes} bytes)"
            ),
            f"Total time: {result.total_elapsed_seconds:.3f} s",
            f"Throughput: {result.throughput_mib_per_second:.3f} MiB/s",
            self._format_latency("Cold", result.cold_latency),
            self._format_latency("Warm", result.warm_latency),
        ]
        failures = [sample for sample in result.samples if not sample.succeeded]
        if failures:
            lines.append("Failures:")
            lines.extend(
                f"  Request {sample.index}: {sample.error}" for sample in failures
            )
        return "\n".join(lines)

    @staticmethod
    def _format_latency(label: str, stats: LatencyStatistics) -> str:
        if stats.count == 0:
            return f"{label} latency: no samples"
        return (
            f"{label} latency (n={stats.count}): "
            f"min={stats.minimum_seconds:.3f}s "
            f"median={stats.median_seconds:.3f}s "
            f"mean={stats.mean_seconds:.3f}s "
            f"stdev={stats.stdev_seconds:.3f}s "
            f"p95={stats.p95_seconds:.3f}s"
        )
