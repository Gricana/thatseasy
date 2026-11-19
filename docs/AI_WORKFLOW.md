# AI-assisted development workflow

## How the task was formalized

The written request was translated into checkable requirements: explicit
layers, dependency direction, an injectable HTTP port, sequential requests,
timeouts and retries, partial-failure handling, metrics, CLI flags, exit
codes, and unit tests that do not require external network access.

The prompt referred to a full monolithic source file, but that version was not
available in the workspace. Rather than claim compatibility by guesswork, the
assistant asked for the source or permission to infer behavior. The user chose
to proceed from the listed requirements; the resulting assumptions are
recorded in [SPECIFICATION.md](SPECIFICATION.md) and [CHANGELOG.md](../CHANGELOG.md).

## Role of the AI agent

The AI agent was used to:

1. Decompose the requirements and identify ambiguities before implementation.
2. Propose a small Clean Architecture layout and compare alternatives such as
   `Protocol` versus an abstract base class and synchronous versus async I/O.
3. Draft the modules, CLI, reporters, tests, and supporting documentation.
4. Review the implementation against the requested behavior and run
   verification commands.

The AI agent is not evidence that the author understands the result. The
developer remains responsible for reviewing the code, explaining the
decisions, and checking that the measured quantities match the benchmark
question.

## Verification actually performed

During implementation, the agent ran standard-library unit tests, including
fake-client tests and a loopback HTTP test for retry behavior; strict mypy
checks; package installation in a virtual environment; and `pip check`.
Those checks passed at that point. The decimal-MB report field and its focused
presentation test were added afterward, and that particular test run was
cancelled; it should be run before treating the latest output change as
verified:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
mypy --strict bench_download tests/domain tests/application tests/infrastructure tests/presentation
```

No external benchmark URL is used in the test suite. Live download results
remain sensitive to server load, caching, network routing, redirects, and
connection reuse.


## Further work if scope expands

1. **Measurement quality:** run repeated batches; define warm-up and actual
   connection reuse; distinguish decoded body bytes from wire bytes and
   successful bytes from partial failed downloads. Ten samples make p95
   unreliable.
2. **Reliability:** add a total deadline and response-size limit; test
   timeouts, redirects, retry exhaustion, and interrupted streams. If retrying
   a partial download, restart the whole GET and avoid double-counting bytes.
3. **Security:** if exposed as a service, prevent SSRF and DNS rebinding,
   validate redirect destinations, and cap duration, response size, and
   concurrency.
