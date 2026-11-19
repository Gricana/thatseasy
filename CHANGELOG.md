# Changelog

## 0.1.0

- The referenced `bench_download.py` monolith and its exact output examples
  were not present in the workspace or request. This package implements the
  listed behavior; text/JSON field names and formatting are therefore newly
  defined rather than claimed as byte-for-byte compatible.
- p95 uses the nearest-rank definition; stdev is sample standard deviation
  and is `0.0` for one observation. Empty warm samples report null metrics in
  JSON and "no samples" in text.
- A failed logical request contributes its latency but contributes zero bytes;
  only complete non-empty response bodies count toward throughput.
- `--json` takes precedence over `--quiet`; JSON remains available for
  automation. Human-readable reports show only the host and port to avoid
  logging URL credentials, paths, or query tokens.
