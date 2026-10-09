# 05. Test double taxonomy & strategy

Read `docs/02-test-doubles.md` first — this module is that taxonomy made concrete
against one real collaborator (`PaymentGateway`) and one real orchestrator
(`OrderService`).

## What's in `examples/`

`conftest.py` builds a small, hand-rolled in-memory `UnitOfWork` (`FakeUnitOfWork`),
`Clock` (`FakeClock`), and idempotency lock (`FakeIdempotencyLock`) — the generic
harness this module and 06-08 all reuse to exercise `OrderService` without a real
database, Redis, or clock. **Read its module docstring** — it documents a real,
deliberate fidelity gap (no transaction rollback) that becomes the exact motivation
for module 09's integration tests. Understanding that gap *is* part of this lesson.

`test_five_ways.py` then tests `OrderService.place_order` against the same scenario
five times, once per kind of test double, with a class implementing each:

| Double | What it proves | Notice |
| --- | --- | --- |
| `DummyPaymentGateway` | Payment is never attempted when stock fails first | Both methods raise if called at all |
| `StubPaymentGateway` | The happy path reaches `PAID` | Canned answer, nothing recorded |
| `SpyPaymentGateway` | The *correct amount and reference* were sent | Records calls; test asserts after the fact |
| `FakePaymentGateway` | Large charges are declined, small ones succeed | Has real decision logic, not a canned answer -- the difference from a stub |
| `ExpectingMockPaymentGateway` | The call shape is exactly right, enforced up front | Fails at call time if wrong, and via `.verify()` if the expected call never happened |

## The habit to build

Before writing a test, ask: *which of these five do I actually need?* — not "let me
mock this." A dummy proves absence of a call; a stub gets you to a result; a spy
lets you inspect calls after the fact; a fake gives you real (if simplified) behavior
your test can rely on; a strict mock is for when the *shape of the interaction
itself* is the contract you're protecting. Reaching for the heaviest tool (a strict
mock, or `unittest.mock` with elaborate `assert_called_with` chains — module 06) by
default, when a plain stub would do, makes tests more fragile than they need to be.

## Exercise

```bash
make ex M=05
```

## You should now be able to

- Name which of the five test-double kinds a given test double actually is, from
  reading its code.
- Explain the difference between a stub and a fake in your own words.
- Explain, using this module's `FakeUnitOfWork` as the example, why a fake's
  fidelity gaps matter and where the corresponding real test should live.

## References

- `docs/02-test-doubles.md`
- Meszaros, "Test Double" — <http://xunitpatterns.com/Test%20Double.html>
- Fowler, "Mocks Aren't Stubs" — <https://martinfowler.com/articles/mocksArentStubs.html>
