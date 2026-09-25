# 6. Glossary

Quick lookups. Longer treatment of most of these is in `01`-`05`.

**AAA** — Arrange/Act/Assert, the standard three-part test structure. `01`.

**Autospec** — `unittest.mock`'s ability to build a `Mock` whose allowed attributes
and call signatures are constrained to match a real object, so a typo'd method name
or wrong argument count fails the test instead of silently returning another `Mock`.
`06`.

**Branch coverage** — did each `if`/`except`/boolean-branch execute, in both
directions, at least once. Stricter than line coverage. `04`, `12`.

**Contract test** — verifies your code's assumptions about an external API's
shape/behavior, independent of a full E2E call. `01`.

**Fake** — a working, simplified real implementation of a dependency (e.g. an
in-memory repository) used in place of the real one. `02`.

**FIRST** — Fast, Independent, Repeatable, Self-validating, Timely: what a unit test
should be. `01`.

**Fixture** — pytest's mechanism for providing setup/teardown and test inputs via
dependency injection into test functions. `03`.

**Flaky test** — passes and fails nondeterministically on unchanged code. `04`.

**Idempotency key** — a client-supplied token that lets a server recognize "this is
a retry of the same request," rather than a new one. `05`, `services/orders.py`.

**Mock (strict sense)** — a test double pre-programmed with expectations that fails
the test itself if unmet. Colloquially, "mock" = "any test double." `02`.

**Mutation testing** — automatically introduces bugs into your code and reruns your
suite, to check whether your tests would actually catch them. `04`.

**Parametrize** — running the same test body against a table of different
inputs/expected-outputs. `02`.

**Protocol** — Python's structural-typing interface (`typing.Protocol`): anything
with the right methods satisfies it, no inheritance required. Used throughout
`src/shop` as the seam fakes/mocks substitute at.

**Regression test** — a test added because a specific bug happened, to prevent its
silent return. `01`.

**Sociable vs. solitary unit test** — sociable: real (fast) collaborators allowed;
solitary: every collaborator is a double. `02`.

**Spy** — a test double that records calls made to it for later assertion. `02`.

**Stub** — a test double that returns canned answers, with no call-tracking. `02`.

**Test double** — umbrella term for dummy/stub/spy/mock/fake (Meszaros). `02`.

**Testcontainers** — a library that starts real Docker containers (Postgres, Redis,
...) from a test suite, and tears them down after. `10`.

**Unit of Work** — a pattern bundling several repository operations into one atomic
transaction. `src/shop/db/uow.py`.
