import unittest

from bench_download.application.ports import HttpClientError
from bench_download.application.run_benchmark import RunBenchmarkUseCase


class FakeHttpClient:
    def __init__(self, outcomes: list[list[int | Exception]]) -> None:
        self.outcomes = outcomes
        self.max_retries = 0
        self.calls = 0
        self.attempts: list[int] = []

    def configure_retries(self, max_retries: int) -> None:
        self.max_retries = max_retries

    def download(
        self, url: str, *, connect_timeout: float, read_timeout: float
    ) -> int:
        del url, connect_timeout, read_timeout
        plan = self.outcomes[self.calls]
        self.calls += 1
        for attempt, outcome in enumerate(plan, 1):
            self.attempts.append(attempt)
            if isinstance(outcome, Exception):
                if attempt > self.max_retries:
                    raise HttpClientError(str(outcome)) from outcome
                continue
            return outcome
        raise HttpClientError("simulated failure")


class RunBenchmarkTests(unittest.TestCase):
    def test_keeps_running_after_failure_and_passes_retry_policy(self) -> None:
        client = FakeHttpClient(
            [
                [10],
                [HttpClientError("temporary"), 20],
                [HttpClientError("unavailable"), HttpClientError("unavailable")],
            ]
        )

        result = RunBenchmarkUseCase(client).execute(
            "https://example.test/image",
            count=3,
            connect_timeout=1.0,
            read_timeout=2.0,
            max_retries=1,
        )

        self.assertEqual(client.max_retries, 1)
        self.assertEqual(client.calls, 3)
        self.assertEqual(client.attempts, [1, 1, 2, 1, 2])
        self.assertEqual(result.successful_count, 2)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.total_bytes, 30)
        self.assertEqual(result.cold_latency.count, 1)
        self.assertEqual(result.warm_latency.count, 2)
        self.assertGreater(result.total_elapsed_seconds, 0)

    def test_rejects_invalid_parameters_before_client_calls(self) -> None:
        client = FakeHttpClient([])

        with self.assertRaisesRegex(ValueError, "at least one"):
            RunBenchmarkUseCase(client).execute(
                "https://example.test/",
                count=0,
                connect_timeout=1.0,
                read_timeout=1.0,
                max_retries=0,
            )

        self.assertEqual(client.calls, 0)
