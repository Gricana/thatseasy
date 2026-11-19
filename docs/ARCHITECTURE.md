# Architecture and implementation constraints

## Dependency direction

```text
main / composition root
  ├── presentation (CLI and reporters)
  ├── infrastructure (requests adapter and URL validation)
  └── application (use case)
         ├── HttpClient Protocol
         └── domain (models and statistics)
```

- **Domain** contains immutable `RequestSample` and `BenchmarkResult` values,
  latency calculations, and derived throughput/size. It imports only itself
  and the Python standard library.
- **Application** owns `RunBenchmarkUseCase` and the `HttpClient` outbound
  port. Constructor injection permits a fake client in unit tests.
- **Infrastructure** implements the port with `requests.Session`,
  `HTTPAdapter`, and `urllib3.Retry`; URL parsing and validation also live
  here.
- **Presentation** parses and validates CLI option syntax and renders text or
  JSON. It has no dependency on `requests`.
- **`main.py`** is the composition root: it validates the input URL, creates
  the concrete adapter, injects it into the use case, and chooses a reporter.
  `__main__.py` only invokes that entrypoint.

`HttpClient` is a `typing.Protocol`: the application relies on the required
operations, not on a base class. This keeps the fake test client small and
avoids inheritance requirements or a DI framework.

## Decisions and alternatives

### Sequential execution

The requested measurement is sequential: each body must be fully consumed
before the next logical request. `asyncio` with sequential awaits would still
wait for each network operation and would add complexity without changing the
workload. Concurrent `gather` would measure parallel load instead. Therefore
the CLI uses synchronous calls; a parallel benchmark would be a separate,
explicit mode.

### Session and streaming

One `requests.Session` owns the connection pool for a run. Responses are read
in 64 KiB chunks to keep memory independent of total response size. Counting
observed body chunks avoids trusting `Content-Length`, but it measures
application-visible response bytes, not HTTP/TLS/IP wire bytes.

### Retry and failure semantics

Retries are configured on the infrastructure adapter because retry behavior
belongs to HTTP transport. The application sees one logical request result.
Only GET is retryable; configured status codes and retry count are centralized
in configuration. If an error is surfaced after response streaming begins,
the use case records a failed logical request and continues; it does not
replay a partially consumed response itself.

### Metric conventions

The first request is labeled cold and later samples warm for reporting. This
is a convenient grouping, not a claim that every later request reused the
same TCP/TLS connection. p95 uses nearest rank; stdev is the sample form.
Downloaded size uses decimal MB, while throughput remains binary MiB/s and is
explicitly labeled.

### Kept out of scope

- No concurrency, async runtime, web framework, database, queue, or DI
  container.
- No writes of downloaded bodies to disk.
- No retries that silently turn a failed logical request into an unbounded
  operation; retries are capped by `--max-retries`.
- No silent fallback values for invalid inputs or failed measurements.
- No public-service SSRF policy: this is a local CLI. If exposed through a
  service, URL/IP allowlisting, redirect validation, and stricter resource
  limits would be mandatory.

## Operational limits

- Connect and read timeouts are socket-level timeouts, not one end-to-end
  deadline. A server that continues sending data can keep a response alive
  beyond the read timeout.
- There is no response-size cap. The streaming implementation bounds memory,
  but not total bytes or total runtime.
- A ten-sample run is enough for a simple exercise, but p95 and stdev are
  noisy at small sample counts. Repeated runs and stable test endpoints are
  needed for defensible comparisons.
- The default User-Agent and retry policy are configurable constants; they do
  not guarantee a server will permit or behave identically across repeated
  requests.
