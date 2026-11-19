# bench-download

`bench-download` is a sequential HTTP(S) download benchmark. It uses a pooled
`requests.Session`, retries transient connection/read and selected HTTP status
failures, consumes each response body before starting the next request, and
reports cold/warm latency statistics and aggregate throughput.

The initial monolithic source described in the refactoring request was not
available in the workspace. Therefore the output schema and p95 convention
are newly specified in [CHANGELOG.md](CHANGELOG.md), not claimed to match an
unseen implementation.

## Project structure

```text
bench_download/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── docs/
│   ├── README.md
│   ├── SPECIFICATION.md
│   ├── ARCHITECTURE.md
│   └── AI_WORKFLOW.md
├── bench_download/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── config.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── statistics.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── ports.py
│   │   └── run_benchmark.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── http_client.py
│   │   └── url_validation.py
│   └── presentation/
│       ├── __init__.py
│       ├── cli.py
│       └── reporters.py
└── tests/
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── presentation/
```

- **domain** owns immutable samples/results and pure latency/throughput
  calculations; it does not depend on HTTP, CLI, or application code.
- **application** defines the `HttpClient` port and coordinates sequential
  requests through constructor injection; it does not know `requests`.
- **infrastructure** adapts `requests.Session` and `urllib3.Retry` to the port,
  and validates HTTP(S) addresses before network access.
- **presentation** parses CLI options and renders text or JSON without knowing
  the HTTP implementation.
- **main.py / __main__.py** manually wire the outer adapters and invoke the
  use case, keeping dependency direction explicit.

This separation keeps metric tests independent of networking and allows the
use case to be tested with a small fake client. `HttpClient` is a `Protocol`
because structural typing makes that fake easy to substitute without
inheritance or a runtime framework.

## Project documentation

- [Specification and acceptance criteria](docs/SPECIFICATION.md)
- [Architecture, design choices, and constraints](docs/ARCHITECTURE.md)
- [AI-assisted development workflow and verification record](docs/AI_WORKFLOW.md)

## Install and run

Python 3.10 or newer is required.

Create an isolated environment first. This avoids installing into the
operating-system-managed Python environment (for example, Debian/Ubuntu PEP
668 installations):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m bench_download https://example.com/large-image.jpg
```

By default, the tool makes 10 logical requests. Each request uses a 5-second
connect timeout, a 30-second read inactivity timeout, and up to 3 retries.
Options:

```text
bench-download URL [-n COUNT] [--connect-timeout SECONDS]
                   [--read-timeout SECONDS] [--max-retries COUNT]
                   [--json] [-q|--quiet]
```

Examples:

```bash
python -m bench_download https://example.com/image.jpg -n 5 \
  --connect-timeout 3 --read-timeout 20 --max-retries 2
python -m bench_download https://example.com/image.jpg --json
```

The downloaded size is reported in **MB** (decimal megabytes, 1 MB =
1,000,000 bytes), with the exact byte count alongside it. Throughput is
**MiB/s**, where 1 MiB = 1,048,576 bytes. It is the bytes from successful,
complete response bodies divided by total wall-clock benchmark time, including
connection attempts and retry backoff. An individual logical request is timed
across its retries. The first request is reported as cold; subsequent requests
are warm. Requests are sequential; retries are internal to one logical
request.

Latency summaries use sample standard deviation (`0.0` for one sample) and
nearest-rank p95. Failed requests remain in the latency summaries but
contribute zero downloaded bytes. JSON output reports null statistics for an
empty warm sample set. `--json` takes precedence over `--quiet`. Reports show
the target authority only, not URL credentials, path, or query values.

The read timeout is an inactivity timeout, not a hard deadline for a complete
response. There is no response-size cap. This CLI is intended for URLs you are
authorized to access; do not expose it as a public URL-fetching service without
additional SSRF controls and resource limits.

## Tests

Run the unit tests without accessing external services. The HTTP retry test
uses only a loopback server:

```bash
python -m unittest discover -s tests -v
```

For strict type checking, install the development extras and run:

```bash
python -m pip install -e ".[dev]"
mypy --strict bench_download
```
