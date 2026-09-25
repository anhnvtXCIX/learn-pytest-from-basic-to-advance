# CLAUDE.md

Conventions for working in this repo, whether that's a future Claude Code session or
a human contributor.

## What this repo is

A pytest curriculum (basics -> advanced mocking -> advanced integration testing),
built around one realistic app: `src/shop`, an async FastAPI + SQLAlchemy Orders
service. See `README.md` for the syllabus and `docs/` for the testing-theory half.

## Module structure (don't break this)

Every `modules/NN-topic/` directory has the same four things:

- `README.md` -- theory, pitfalls, references, "you should now be able to..."
- `examples/` -- passing, heavily-commented reference tests (and a local
  `conftest.py` if the module needs its own fixtures)
- `exercises/` -- TODO tests, auto-marked `exercise` by the root `conftest.py`
  (anything collected from a path containing `exercises/`), deselected by default
- `solutions/` -- reference answers to `exercises/`, same marker, same deselection

`make test` must stay green with **no Docker running and no network access**. If you
add a test that needs either, mark it `docker` (deselected the same way) or put it
somewhere that isn't collected by default.

## The app (`src/shop`)

Layered on purpose -- `domain` (pure) / `db` (SQLAlchemy) / `gateways` (external
HTTP + Redis) / `services` (orchestration) / `api` (FastAPI) -- because the layering
*is* the lesson: each layer has a different testing story. Don't collapse layers to
"simplify" an example; the seams are the point. See `src/shop/__init__.py` and
`docs/05-backend-testing-playbook.md`.

Two deliberately dialect-sensitive spots, used by module 10: `ProductRepository.reserve_stock`
uses `.with_for_update()`, which SQLite silently ignores (verified empirically, not
assumed); `OrderRow.idempotency_key` is UNIQUE, and the two backends report a
violation differently.

Known async-SQLAlchemy trap already hit once while building this: relationships
(`OrderRow.lines`) need `selectinload()`/`joinedload()` -- implicit lazy loading raises
`MissingGreenlet` outside of a query context. If you add a new query that touches a
relationship, eager-load it.

## Conventions

- Python 3.13, managed with `uv` (not pip/poetry). `uv sync` installs everything,
  including an editable install of `shop` itself (see the `[tool.hatch.build...]`
  comment in `pyproject.toml` for why that's needed given the project/package name
  mismatch).
- Money is always integer cents. Never introduce a `float` for a monetary value.
- New domain exceptions go in `src/shop/domain/errors.py` and get translated to HTTP
  in `src/shop/api/routes.py` -- never raise `HTTPException` from `services/` or below.
- `testkit/` (the shared fixture/factory package) is deliberately built *in* module
  13, not before -- earlier modules define fixtures locally in their own
  `examples/conftest.py`, even at the cost of some duplication, because module 13's
  lesson is "notice the duplication, then extract it." Don't pre-empt that by
  centralizing fixtures earlier.
- Every reference to a specific library version, API behavior, or "X does Y" claim
  in `docs/` or a module `README.md` should be something that was actually checked
  (docs, changelog, or an empirical test), not remembered from general training.
  Library APIs move fast enough that this matters.
