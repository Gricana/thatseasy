# Specification

## Purpose

Measure sequential HTTP(S) downloads from one caller-supplied URL and report
the outcome, response-body volume, latency distributions, and aggregate
throughput. The command is a local CLI, not a network service.

## Inputs and defaults

| Input | Default | Constraint |
|---|---:|---|
| URL | Required | Absolute HTTP or HTTPS URL with a hostname and valid port |
| `-n` / `--requests` | 10 | Positive integer; number of logical requests |
| `--connect-timeout` | 5 seconds | Finite positive number |
| `--read-timeout` | 30 seconds | Finite positive number; socket inactivity timeout |
| `--max-retries` | 3 | Non-negative integer; retries per logical request |
| `--json` | Off | Emit machine-readable JSON |
| `-q` / `--quiet` | Off | Suppress text output; JSON still takes precedence |

The default User-Agent is `bench-download/0.1`. The HTTP adapter streams in
64 KiB chunks. Retry backoff uses a factor of 0.5 seconds and applies to GET
requests for configured transient connection/read errors and status codes
429, 500, 502, 503, and 504.

## Request behavior

1. Validate the initial URL before starting network traffic.
2. Execute the requested number of logical GETs sequentially. A logical
   request must finish, fail, or exhaust its transport retries before the
   next one starts.
3. Use one `requests.Session` for the run, allowing connection-pool reuse when
   the server and connection permit it. Use separate connect and read
   inactivity timeouts.
4. Require a successful HTTP status and a non-empty response body.
5. Stream and count chunks instead of buffering the entire body in memory.
6. Preserve each terminal request failure in the result and continue with the
   next logical request. A failed/incomplete response contributes zero bytes;
   only complete successful bodies contribute to the total.
7. Return exit code 0 if all logical requests succeed, 1 for an invalid URL or
   any request failures. `argparse` handles malformed CLI arguments with its
   standard usage-error exit code.

## Metric definitions

- **Downloaded size:** sum of bytes yielded by `requests.Response.iter_content`
  for successful complete responses. Text reports decimal MB
  (`1 MB = 1,000,000 bytes`) and exact bytes. JSON includes both.
- **Throughput:** successful response-body bytes divided by total wall-clock
  run time, in MiB/s (`1 MiB = 1,048,576 bytes`). The interval includes
  connection setup, server wait, and any retry backoff.
- **Request latency:** elapsed time for one logical request, including its
  retries and retry backoff.
- **Cold latency:** statistics for the first logical request in the run.
- **Warm latency:** statistics for all logical requests after the first.
  “Warm” is an ordinal label, not proof that a pooled connection was reused.
- **Min / median / mean:** minimum, median, and arithmetic mean of the latency
  samples in that group.
- **Stdev:** sample standard deviation; defined as zero for one sample.
- **p95:** nearest-rank 95th percentile, at index
  `ceil(0.95 * sample_count) - 1` in the sorted samples. With small samples it
  may equal the maximum and should not be treated as a stable population
  estimate.
- Empty warm groups have count zero and null JSON statistics; text says
  “no samples”.

## Acceptance criteria

- Domain statistics can be tested using only values, without network mocks.
- The application use case accepts an injected `HttpClient` and executes
  logical requests sequentially.
- The HTTP adapter uses connection pooling, separate timeouts, retry policy,
  status validation, streaming, and empty-body validation.
- A terminal failure does not abort later logical requests.
- Text and JSON reports expose consistent totals, latency groups, and
  throughput units.
- Invalid initial URLs fail before an HTTP request is made.
- Tests cover pure statistics, application orchestration with a fake client,
  HTTP adapter behavior, and retry handling against a loopback server.
