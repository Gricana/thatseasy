"""CLI parser and application composition root."""

from __future__ import annotations

import argparse
import math
from collections.abc import Sequence
from dataclasses import dataclass

from bench_download.config import (
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_READ_TIMEOUT_SECONDS,
    DEFAULT_REQUEST_COUNT,
)


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least one")
    return parsed


def _non_negative_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return parsed


def _positive_timeout(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and positive")
    return parsed


@dataclass(frozen=True, slots=True)
class CliOptions:
    """Validated options consumed by the composition root."""

    url: str
    requests: int
    connect_timeout: float
    read_timeout: float
    max_retries: int
    json: bool
    quiet: bool


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser in one place to keep defaults visible."""
    parser = argparse.ArgumentParser(
        prog="bench-download",
        description="Measure sequential HTTP download latency and throughput.",
    )
    parser.add_argument("url", help="absolute HTTP(S) URL to download")
    parser.add_argument(
        "-n",
        "--requests",
        type=_positive_integer,
        default=DEFAULT_REQUEST_COUNT,
        metavar="COUNT",
    )
    parser.add_argument(
        "--connect-timeout",
        type=_positive_timeout,
        default=DEFAULT_CONNECT_TIMEOUT_SECONDS,
        metavar="SECONDS",
    )
    parser.add_argument(
        "--read-timeout",
        type=_positive_timeout,
        default=DEFAULT_READ_TIMEOUT_SECONDS,
        metavar="SECONDS",
    )
    parser.add_argument(
        "--max-retries",
        type=_non_negative_integer,
        default=DEFAULT_MAX_RETRIES,
        metavar="COUNT",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress text output (JSON output is still emitted with --json)",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> CliOptions:
    """Parse input without constructing application or infrastructure objects."""
    parsed = build_parser().parse_args(argv)
    return CliOptions(
        url=parsed.url,
        requests=parsed.requests,
        connect_timeout=parsed.connect_timeout,
        read_timeout=parsed.read_timeout,
        max_retries=parsed.max_retries,
        json=parsed.json,
        quiet=parsed.quiet,
    )
