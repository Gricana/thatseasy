import json
import unittest

from bench_download.domain.models import BenchmarkResult, RequestSample
from bench_download.presentation.reporters import JsonReporter, TextReporter


class ReporterTests(unittest.TestCase):
    def test_reports_downloaded_size_in_decimal_megabytes(self) -> None:
        result = BenchmarkResult(
            url="https://example.test/image",
            requested_count=1,
            samples=(RequestSample(1, 0.25, 1_500_000),),
            total_elapsed_seconds=0.5,
        )

        text = TextReporter().render(result)
        payload = json.loads(JsonReporter().render(result))

        self.assertIn("Downloaded: 1.500 MB (1500000 bytes)", text)
        self.assertEqual(payload["total_megabytes"], 1.5)


if __name__ == "__main__":
    unittest.main()
