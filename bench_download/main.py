"""Manual dependency wiring for the command-line application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from bench_download.application.run_benchmark import RunBenchmarkUseCase
from bench_download.config import DEFAULT_USER_AGENT
from bench_download.infrastructure.http_client import RequestsHttpClient
from bench_download.infrastructure.url_validation import UrlValidationError, validate_url
from bench_download.presentation.cli import parse_args
from bench_download.presentation.reporters import JsonReporter, TextReporter


def main(argv: Sequence[str] | None = None) -> int:
    """Wire the outer adapters to the use case and return its process status."""
    args = parse_args(argv)
    try:
        validate_url(args.url)
    except UrlValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    with RequestsHttpClient(user_agent=DEFAULT_USER_AGENT) as http_client:
        result = RunBenchmarkUseCase(http_client).execute(
            args.url,
            count=args.requests,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
            max_retries=args.max_retries,
        )

    if args.json:
        print(JsonReporter().render(result))
    elif not args.quiet:
        print(TextReporter().render(result))
    return 1 if result.failed_count else 0
