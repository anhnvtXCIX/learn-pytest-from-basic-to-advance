# 08. Mocking HTTP boundaries with respx

Module 06 mocked `httpx.AsyncClient` itself with `create_autospec`. This module
covers a different, often better, tool for the same job: **respx**, which mocks
*underneath* `httpx` instead of replacing it.

## Why respx instead of a mocked client

`create_autospec(httpx.AsyncClient)` (module 06) replaces the whole client. That
means none of `httpx`'s own logic runs: no real URL joining (`base_url` +
path), no real header merging, no real JSON encoding. If `HttpPaymentGateway`
had a bug in its URL — say, a missing leading slash that silently changed where
the request actually went — an autospec'd-client test wouldn't notice, because
your test never asked httpx to build a URL at all; it just recorded what
arguments you *told* the mock you called.

respx instead installs a custom transport at the bottom of a *real*
`httpx.AsyncClient`. Your production code runs entirely unmodified up to the
point of actually opening a socket — real URL construction, real header
merging, real JSON serialization — and respx intercepts just before the bytes
would hit the network, matching the request against routes you declare and
returning a canned response. `examples/test_respx_catches_url_bugs.py` proves
this concretely: the exact same test setup, run against a `HttpPaymentGateway`
with a deliberately wrong URL, fails with "no route matched" — a bug an
autospec'd-client test would have missed entirely.

## Basic route matching

```python
import respx
import httpx

@respx.mock
async def test_charge_succeeds():
    respx.post("https://payments.example.com/v1/charges").mock(
        return_value=httpx.Response(201, json={"payment_reference": "pay_abc"})
    )
    ...
```

`@respx.mock` (or the `respx_mock` fixture from `pytest-respx`... this repo uses the
decorator/context-manager form directly) activates interception for the test;
anything not matched by a declared route raises, so a request going somewhere
unexpected fails loudly instead of silently hitting the real network.

## Asserting on the request that was actually sent

`route.calls.last.request` gives you the real, fully-constructed `httpx.Request` —
inspect `.url`, `.headers`, and `.content` (raw bytes; `json.loads()` it, or use
`httpx.Request`'s own helpers) to assert on exactly what your code sent, the same
"spy" idea from module 05, now backed by a real request object instead of whatever
your own code happened to pass to a mock.

## Simulating timeouts and 5xx

```python
respx.post(url).mock(side_effect=httpx.TimeoutException("timed out"))
respx.post(url).mock(return_value=httpx.Response(500))
```

Both should map to `PaymentGatewayUnavailableError` per `HttpPaymentGateway`'s own
translation logic — this is the right layer to test that translation, since it's
`HttpPaymentGateway`'s job specifically (`OrderService` never sees an `httpx`
exception at all, by design).

## Why `OrderService` doesn't retry a failed charge itself

Worth understanding, since it's the kind of design decision an interviewer will ask
about: automatically retrying `charge()` after a timeout is dangerous, because a
timeout doesn't tell you whether the first attempt *actually* succeeded on the
gateway's side before the response was lost — retrying blindly risks a double
charge. The safe way to retry is to resend the **same idempotency key** (this
repo's `HttpPaymentGateway.charge` sends the idempotency key as `reference`) and let
the payment gateway's own idempotency handling recognize the retry — which is a
*client-level* retry decision (module 11 territory, or genuinely the caller's
responsibility), not something `OrderService` should paper over silently.

## The limit of any HTTP-level test double, respx included

respx (like a fake, like an autospec'd mock) only ever tests your code against
*your own assumptions* about the payment gateway's contract. If the real API
changes its response shape, every respx test keeps passing right up until
production breaks. This is exactly `docs/05-backend-testing-playbook.md`'s "three
options for external services" — respx is deliberately #2 (test your adapter),
never a substitute for #3 (occasional real-sandbox contract tests). See
`docs/07-resources.md` for `schemathesis`/`Pact` if you need to close that gap for
real.

## Exercise

```bash
make ex M=08
```

## You should now be able to

- Explain concretely (not just "respx is better") what respx exercises that a fully
  mocked client doesn't.
- Write a respx test asserting on the real request body that was sent.
- Simulate a timeout and a 5xx with respx and assert the correct domain exception.
- Explain why blind automatic retry of a payment charge is dangerous.

## References

- respx docs — https://lundberg.github.io/respx/
- httpx docs, `MockTransport` — https://www.python-httpx.org/advanced/transports/#mock-transports
