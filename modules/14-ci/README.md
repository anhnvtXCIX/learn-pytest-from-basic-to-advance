# 14. CI

`.github/workflows/ci.yml` is real, working CI for this repo — three jobs, run on
every push and PR. This module explains the choices in it, all of which were
verified by running the exact same commands locally before trusting them to CI.

## Three jobs, not one

- **`test`** — the fast tier: unit + SQLite-backed integration (modules 00-09,
  11-13). No Docker, no external services, and it should stay fast enough that
  nobody is ever tempted to skip waiting for it.
- **`test-docker`** — module 10's Testcontainers-based Postgres/Redis tests, as a
  **separate job**, not a step tacked onto `test`. Two reasons: its result and
  timing are visible independently (a slow or flaky container pull shouldn't muddy
  the fast job's signal), and GitHub's own Ubuntu runners already ship a usable
  Docker daemon — Testcontainers manages its own containers programmatically, so
  there's no `services:` block here the way a project *not* using Testcontainers
  would need (a `services:` block starts long-lived containers alongside the job;
  Testcontainers starts and tears down its own, which is exactly the tradeoff
  `docs/05-backend-testing-playbook.md` and module 10 discuss for local dev too).
- **`lint`** — `ruff check` + `mypy`, kept separate from `test` so a lint failure and
  a test failure are two different red X's, not one job you have to read the log of
  to tell apart.

## `uv sync --locked`

Not `uv sync`. `--locked` fails the build if `uv.lock` doesn't match
`pyproject.toml` exactly, instead of silently re-resolving and installing something
slightly different than what's committed — the CI equivalent of "don't let the
lockfile drift without anyone noticing."

## The coverage floor: `--fail-under=70`, not a rounder 80 or 90

Chosen by actually running `make cov` against this repo's own example tests (75% at
the time this was written — check `htmlcov/index.html` or the terminal report
yourself, it'll drift as the repo grows) and setting the floor a little below that
real, measured number. An arbitrary round number picked without measuring anything
is either meaninglessly low (never catches a real regression) or an immediate,
noisy failure the moment someone checks — neither is useful. Revisit this number
periodically as real coverage grows; don't chase it upward by adding low-value tests
just to move the gate (`docs/04-coverage-and-quality.md`).

## JUnit XML, uploaded even on failure

`--junitxml=junit.xml` produces a standard machine-readable test report (which test
ran, how long, pass/fail/error, with tracebacks) that CI dashboards, flaky-test
trackers, and other tooling can consume without parsing pytest's terminal output.
`if: always()` on the upload step means the report is available **even when the job
failed** — the run you most want to inspect closely is exactly the one a naive
`if: success()` would hide it for.

## Exercise

```bash
make ex M=14
```

## You should now be able to

- Explain why `test` and `test-docker` are separate jobs.
- Explain what `uv sync --locked` protects against that plain `uv sync` doesn't.
- Read a coverage report and set a floor tied to a real measurement, not a guess.
- Explain what JUnit XML is for and why it's uploaded unconditionally.

## References

- GitHub Actions docs — https://docs.github.com/en/actions
- `astral-sh/setup-uv` — https://github.com/astral-sh/setup-uv
- pytest docs, `--junitxml` — https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files
- coverage.py docs, `report --fail-under` —
  https://coverage.readthedocs.io/en/latest/cmd.html#coverage-report
