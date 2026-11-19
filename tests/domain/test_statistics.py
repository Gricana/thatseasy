import math
import unittest

from bench_download.domain.statistics import calculate_latency_statistics


class LatencyStatisticsTests(unittest.TestCase):
    def test_calculates_sample_stdev_and_nearest_rank_p95(self) -> None:
        result = calculate_latency_statistics([1, 2, 3, 4, 5])

        self.assertEqual(result.count, 5)
        self.assertEqual(result.minimum_seconds, 1)
        self.assertEqual(result.median_seconds, 3)
        self.assertEqual(result.mean_seconds, 3)
        self.assertAlmostEqual(result.stdev_seconds or 0, math.sqrt(2.5))
        self.assertEqual(result.p95_seconds, 5)

    def test_empty_and_singleton_samples_are_defined(self) -> None:
        empty = calculate_latency_statistics([])
        single = calculate_latency_statistics([2.5])

        self.assertEqual(empty.count, 0)
        self.assertIsNone(empty.p95_seconds)
        self.assertEqual(single.stdev_seconds, 0.0)
        self.assertEqual(single.p95_seconds, 2.5)


if __name__ == "__main__":
    unittest.main()
