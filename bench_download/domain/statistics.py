"""Pure latency-statistics calculations."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class LatencyStatistics:
    """Summary values are ``None`` when the sample set is empty."""

    count: int
    minimum_seconds: float | None
    median_seconds: float | None
    mean_seconds: float | None
    stdev_seconds: float | None
    p95_seconds: float | None


def calculate_latency_statistics(
    durations_seconds: Iterable[float],
) -> LatencyStatistics:
    """Use sample stdev and nearest-rank p95 for explicit, dependency-free metrics."""
    values = tuple(durations_seconds)
    if not values:
        return LatencyStatistics(0, None, None, None, None, None)
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Durations must be finite, non-negative numbers.")

    ordered = sorted(values)
    p95_index = math.ceil(0.95 * len(ordered)) - 1
    return LatencyStatistics(
        count=len(ordered),
        minimum_seconds=ordered[0],
        median_seconds=statistics.median(ordered),
        mean_seconds=statistics.mean(ordered),
        stdev_seconds=statistics.stdev(ordered) if len(ordered) > 1 else 0.0,
        p95_seconds=ordered[p95_index],
    )
