# 2. Test doubles: the vocabulary that makes mocking learnable

"Mocking" is usually used as a catch-all verb for five distinct things. Gerard
Meszaros' taxonomy (from *xUnit Test Patterns*) is the standard reference, and
knowing which double you actually want is most of what makes module 05-08 click.

> Meszaros, "Test Double" — http://xunitpatterns.com/Test%20Double.html
> Fowler, "Mocks Aren't Stubs" — https://martinfowler.com/articles/mocksArentStubs.html

## The five kinds

- **Dummy** — a placeholder passed only because a signature requires it; never
  actually used. E.g. passing `None` or a throwaway object for a parameter the code
  path under test never touches.
- **Stub** — returns canned answers to calls made during the test; has no concept of
  being "checked" afterward. `FakePaymentGateway` returning a fixed reference string
  is acting as a stub when the test only cares about the return value.
- **Spy** — a stub that also records what was called, so the test can assert on it
  afterward (`gateway.charges == [...]`). `unittest.mock.Mock`'s call-recording
  (`.call_args`, `.assert_called_with`) makes every `Mock` usable as a spy for free.
- **Mock** (in the strict, Meszaros sense) — pre-programmed with *expectations*
  about which calls it should receive, and fails the test itself if they're not met.
  `unittest.mock`'s `Mock` blurs stub/spy/mock together, which is convenient but why
  "mock" colloquially means "any test double" in most conversation — module 06 is
  explicit about which behavior you're actually using at each call site.
- **Fake** — a working, simplified implementation of the real thing. An in-memory
  dict-backed repository standing in for a database is a fake: it has real behavior
  (you can insert, then get it back), just not the real backend. Fakes tend to be
  the *most* valuable double for anything with meaningful behavior (a repository, a
  cache) because they let a test exercise real logic (e.g. "does place_order() see
  its own reservation") that a plain stub can't.

## Classicist vs. mockist testing

Two schools, both legitimate, and this repo deliberately teaches both because you'll
meet both in the wild:

- **Classicist (Detroit school)** — prefer real collaborators; reach for a double
  only at expensive/unreliable boundaries (network, real time, real payment
  processor). Verify state, not interactions. Kent Beck, the original xUnit authors.
- **Mockist (London school)** — isolate the unit under test from *all* collaborators
  on every test, verifying the sequence of interactions instead of just end state.
  Forces small, single-responsibility classes as a side effect. Freeman & Pryce,
  *Growing Object-Oriented Software, Guided by Tests*.

> Fowler again has the canonical write-up of both, in the same "Mocks Aren't Stubs"
> article linked above — read the "Classical and Mockist Testing" section.

This repo's `OrderService` tests (module 05 onward) lean classicist: fakes over
interaction-verifying mocks wherever a fake is easy to write, because fakes catch a
class of bug (wrong sequencing between *your own* stateful objects) that a
call-count assertion doesn't. But module 06 also teaches you to assert on calls
directly (`assert_called_once_with(...)`) for cases where the interaction genuinely
*is* the contract — e.g. "did we send the idempotency key as the payment
`reference`."

## "Don't mock what you don't own"

A rule from the London-school community itself, and the single most useful sentence
in this document: **don't write test doubles for types you don't control** (a third
party library's classes, the standard library, an ORM session). If you patch
`httpx.AsyncClient.post` directly, your test now encodes assumptions about httpx's
internals, and passes even if your usage is wrong in a way real httpx would reject.

Instead, wrap the thing you don't own in a small interface you *do* own (a
`Protocol`, an adapter class), and put your test doubles at *that* seam. This repo's
`PaymentGateway` protocol (`src/shop/gateways/payments.py`) exists entirely for this
reason — `OrderService` doubles the *gateway*, never `httpx` itself. Module 08 then
shows the technique for testing the adapter that *does* touch httpx: respx, which
intercepts at the transport level instead of monkeypatching library internals.

## The over-mocking failure mode

Signs a test suite has over-mocked:
- Tests break on every refactor even though behavior didn't change (see
  `01-testing-fundamentals.md`'s "behavior, not implementation").
- A test mocks three or four collaborators just to reach the one line of logic it
  actually cares about — a sign the unit under test is doing too much, or the test
  is at the wrong level (should be a smaller unit test of the inner piece, or a
  sociable test that doesn't isolate so aggressively).
- Passing tests coexist with a broken production system, because every seam where
  two real pieces would have disagreed was mocked away. This is the specific failure
  the integration layer (`docs/01`, pyramid/trophy discussion) exists to catch, and
  why module 05's fakes are deliberately *behaviorally faithful* (a fake repository
  actually enforces "can't reserve more stock than exists") rather than dumb stubs.

## Where this maps in the repo

| Double | Used for | Where |
|---|---|---|
| Dummy | Rare here — most args matter | — |
| Stub | Fixed price feed, fixed clock value | module 07 |
| Spy | Asserting the payment gateway was called with the right amount | module 06 |
| Mock (`unittest.mock`) | Precise call-shape assertions, `autospec` | module 06 |
| Fake | In-memory `ProductRepository`/`OrderRepository`, fake Redis lock | module 05 |
| Real (Testcontainers) | Actual Postgres/Redis behavior modules 05-08 can't fake honestly | modules 10-11 |

## Next

- `03-what-to-test.md` — choosing test cases systematically
- `modules/05-test-double-taxonomy` — the same test, written five ways
