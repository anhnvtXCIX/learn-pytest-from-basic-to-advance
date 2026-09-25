# 2. Test doubles: the vocabulary that makes mocking learnable

"Mocking" is usually used as a catch-all verb for five distinct things. Gerard
Meszaros' taxonomy (from *xUnit Test Patterns*) is the standard reference, and
knowing which double you actually want is most of what makes module 05-08 click.

> Meszaros, "Test Double" — <http://xunitpatterns.com/Test%20Double.html>\
> Fowler, "Mocks Aren't Stubs" — <https://martinfowler.com/articles/mocksArentStubs.html>

## A running example

Everything below uses one tiny function, so you can compare the doubles side by
side. `checkout` charges a card, then emails a receipt:

```python
def checkout(cart_total_cents, gateway, mailer, email):
    if cart_total_cents <= 0:
        raise ValueError("empty cart")
    ref = gateway.charge(cart_total_cents)        # talks to a payment API
    mailer.send(email, f"Paid, ref {ref}")        # talks to an email service
    return ref
```

In production `gateway` calls a real payment API and `mailer` sends real email. You
don't want either in a unit test: they're slow, cost money, and can fail for reasons
unrelated to your code. So each test replaces them with a **test double**. Which kind
depends on *what the test is trying to find out*.

## The five kinds

### 1. Dummy — "I have to pass something, but it's never used"

The empty-cart check raises before `gateway` or `mailer` is ever touched, so the test
doesn't need working ones. It just has to fill the parameter slots.

```python
def test_empty_cart_is_rejected():
    with pytest.raises(ValueError):
        checkout(0, gateway=None, mailer=None, email="a@b.c")
```

`None` is the dummy. If the code *did* touch it, you'd get an `AttributeError` — which
is the point: the test proves those collaborators aren't reached on this path.

### 2. Stub — "When you're asked, answer this"

The test needs `gateway.charge()` to return *something* so `checkout` can continue.
The stub gives a fixed answer, whatever it's asked.

```python
class StubGateway:
    def charge(self, amount_cents):
        return "ref-123"                          # same answer every time

def test_checkout_returns_the_payment_reference():
    ref = checkout(500, StubGateway(), DummyMailer(), "a@b.c")
    assert ref == "ref-123"
```

(`DummyMailer` is a class with a `send` that does nothing — a dummy that must be
callable.) You assert on what came *out*, not on what the stub received.

### 3. Spy — "Do the same, and remember what happened"

Now you want to know: *did the receipt email get sent, and with the right text?* A
spy is a stub that records its calls so the test can look afterward.

```python
class SpyMailer:
    def __init__(self):
        self.sent = []
    def send(self, to, body):
        self.sent.append((to, body))              # remember, don't send

def test_receipt_is_emailed():
    mailer = SpyMailer()
    checkout(500, StubGateway(), mailer, "a@b.c")
    assert mailer.sent == [("a@b.c", "Paid, ref ref-123")]   # inspect afterwards
```

The **test** decides what to check, after the code has run.

### 4. Fake — "A real, working, simplified version"

Sometimes a canned answer isn't enough because the behaviour *depends on state*. A
fake gateway with a balance really declines when you overspend:

```python
class FakeGateway:
    def __init__(self, balance_cents):
        self.balance_cents = balance_cents
    def charge(self, amount_cents):
        if amount_cents > self.balance_cents:
            raise RuntimeError("declined")
        self.balance_cents -= amount_cents
        return f"ref-{amount_cents}"

def test_second_purchase_is_declined_when_funds_run_out():
    gateway = FakeGateway(balance_cents=1000)
    checkout(600, gateway, DummyMailer(), "a@b.c")            # ok, 400 left
    with pytest.raises(RuntimeError):
        checkout(600, gateway, DummyMailer(), "a@b.c")        # 600 > 400
    assert gateway.balance_cents == 400
```

It's a genuine (tiny) implementation, just without the network. Other classic fakes:
an in-memory dict standing in for a database, an in-memory list standing in for a
message queue.

### 5. Mock (strict sense) — "You must be called exactly like this, or the test fails"

A mock is told the expected call **up front** and complains itself — immediately if
called wrongly, and again at the end if never called.

```python
class StrictMailer:
    def __init__(self, expect_to, expect_body):
        self.expected = (expect_to, expect_body)
        self.called = False
    def send(self, to, body):
        assert (to, body) == self.expected, f"unexpected call {(to, body)}"
        self.called = True
    def verify(self):
        assert self.called, "send() was never called"

def test_receipt_call_shape():
    mailer = StrictMailer("a@b.c", "Paid, ref ref-123")
    checkout(500, StubGateway(), mailer, "a@b.c")
    mailer.verify()
```

Python's `unittest.mock.Mock` (module 06) is looser than this: you run the code first,
then ask `mailer.send.assert_called_once_with("a@b.c", "Paid, ref ref-123")`. That is
really spy-style — the check happens *after*. People still call it "a mock", which is
why the word is so confusing.

## Cheat sheet

| Kind | Question the test asks | Returns | Records calls? | Has real logic? |
| --- | --- | --- | --- | --- |
| Dummy | (none — just fills a slot) | nothing | no | no |
| Stub | "Given this answer, does my code work?" | canned value | no | no |
| Spy | "What did my code *do* to this collaborator?" | canned value | **yes** | no |
| Fake | "Does my code work against realistic behaviour?" | computed value | optional | **yes**, simplified |
| Mock | "Was it called *exactly* like this?" | canned value | yes, and enforces | no |

## The two pairs people mix up

**Stub vs. fake** — a stub returns the same thing whatever you send it
(`charge(1)` and `charge(999999)` both give `"ref-123"`). A fake *computes* the answer
from its state (`charge(999999)` is declined). If the test needs behaviour that changes
with input or history, you need a fake.

**Spy vs. mock** — both check calls. A spy records, and the test asserts *after*. A
mock is given the expectation *before*, and fails on its own. Prefer spies (or
`assert_called_with` after the fact): the test reads top-to-bottom as
arrange / act / assert.

## Which one should I reach for?

1. Is the collaborator not reached in this test at all? → **dummy**.
2. Do I just need it to return something so the code can proceed? → **stub**.
3. Do I need to check what my code sent to it? → **spy**.
4. Does the behaviour depend on state or input (stock levels, balances, "already
   exists")? → **fake**.
5. Is the exact call *itself* the requirement, and a spy feels too loose? → **mock**.

Start at 1 and stop at the first "yes" — the simplest double that answers the
test's question is the right one. The full versions of all of these, against this
repo's real `OrderService` and `PaymentGateway`, are in
`modules/05-test-double-taxonomy/examples/test_five_ways.py`.

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
| --- | --- | --- |
| Dummy | Rare here — most args matter | — |
| Stub | Fixed price feed, fixed clock value | module 07 |
| Spy | Asserting the payment gateway was called with the right amount | module 06 |
| Mock (`unittest.mock`) | Precise call-shape assertions, `autospec` | module 06 |
| Fake | In-memory `ProductRepository`/`OrderRepository`, fake Redis lock | module 05 |
| Real (Testcontainers) | Actual Postgres/Redis behavior modules 05-08 can't fake honestly | modules 10-11 |

## Next

- `03-what-to-test.md` — choosing test cases systematically
- `modules/05-test-double-taxonomy` — the same test, written five ways
