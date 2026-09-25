# 3. What to test: choosing cases systematically

Given a function, how do you decide *which* inputs deserve a test, out of infinitely
many? These are the standard black-box techniques — they don't require reading the
implementation, which is exactly why they're good at finding bugs the author didn't
think of. (Contrast with white-box/structural coverage, `04-coverage-and-quality.md`.)

## Equivalence partitioning

Split the input space into classes where, if the code is correct for one member of
the class, it's (probably) correct for all of them — then test one representative
per class instead of every value.

For `calculate_discount_cents(subtotal_cents)` (`src/shop/domain/pricing.py`), the
partitions aren't "small numbers" and "big numbers" — they're the actual tiers: below
the lowest threshold, in the 5% band, in the 10% band, in the 15% band. Module 02's
parametrize exercises use exactly this partitioning.

**Example.** Discount tiers: under $50 → 0%, $50–$99.99 → 5%, $100–$249.99 → 10%,
$250+ → 15%. Four partitions, so four representative tests — not fifty:

| Partition | Representative subtotal | Expected discount |
| --- | --- | --- |
| below all tiers | 2,000 | 0 |
| 5% tier | 7,000 | 350 |
| 10% tier | 15,000 | 1,500 |
| 15% tier | 40,000 | 6,000 |

If it works for 7,000 it will almost certainly work for 7,001 or 8,500.

## Boundary value analysis

Bugs cluster at the edges of partitions (off-by-one errors, `<` vs `<=`), so test
*at* and *adjacent to* every boundary, not just comfortably inside each partition.
For a threshold at 5,000 cents: test 4,999, 5,000, and 5,001 — three cases, not one,
and specifically the three most likely to catch a real mistake.

**Example.** Discount tier edge at 5,000 (verified against `calculate_discount_cents`):

```python
@pytest.mark.parametrize("subtotal, expected", [
    (4_999, 0),      # one below: no discount
    (5_000, 250),    # exactly on the boundary: 5% applies
    (5_001, 250),    # one above: 5% (250.05 rounds to 250)
])
def test_lowest_tier_boundary(subtotal, expected):
    assert calculate_discount_cents(subtotal) == expected
```

A bug like `>` instead of `>=` passes every "comfortably inside" test and fails only
the `5_000` row.

## Decision tables

When behavior depends on a *combination* of independent conditions, list every
combination in a table and derive one test per row (or per row that matters — a full
table can be pruned once you understand which combinations are actually reachable
or actually distinct in outcome). `OrderService.place_order`'s error handling is a
decision-table problem: {product exists?} x {stock sufficient?} x {payment
succeeds?} x {idempotency key already used?} each independently flips the outcome.

**Example.** Two yes/no questions decide what `place_order` does. Every combination
is a row, and each row is one test:

| Product exists? | Enough stock? | Payment OK? | Expected result |
| --- | --- | --- | --- |
| no | – | – | `ProductNotFoundError` (nothing reserved, nothing charged) |
| yes | no | – | `InsufficientStockError` (payment never attempted) |
| yes | yes | no | `PaymentDeclinedError`, stock **released** again |
| yes | yes | yes | order is `PAID`, stock reduced |

Notice "–": once an earlier condition fails, later ones are irrelevant. Writing the
table is what makes that visible, and stops you writing 8 tests where 4 are enough.

## State transition testing

For anything with a lifecycle — `OrderStatus`: `pending -> paid -> refunded`, or
`pending -> cancelled` — enumerate the valid transitions *and* explicitly test the
invalid ones (can you cancel an already-refunded order? Can you pay a cancelled
one?). `InvalidOrderStateError` in this repo exists specifically to make illegal
transitions a tested, intentional error rather than an accident of whatever the code
happens to do. Draw the state diagram before writing the tests if it isn't obvious.

**Example.** An order is created `pending`; a successful charge makes it `paid`; a
declined charge makes it `cancelled` (stock is released); `cancel_order` on a `paid`
order refunds it. Here is what `cancel_order` should do from each state:

| Current status | `cancel_order` should… |
| --- | --- |
| pending | raise `InvalidOrderStateError` (nothing was paid yet) |
| paid | refund the payment, restock, become `refunded` |
| refunded | raise `InvalidOrderStateError` (already done) |
| cancelled | raise `InvalidOrderStateError` |

Three of the four rows are error cells, and they're the ones people forget. "Cancelling
an already-refunded order returns 409" is a real test in module 11.

## Error paths, deliberately, not incidentally

It's easy to write ten tests for the happy path and one vague `pytest.raises`
catch-all for "errors." Treat each distinct failure mode as its own first-class case
with its own assertion on *which* exception and *what* the system state is
afterward (did a partial write happen? was stock released? see
`services/orders.py`'s compensation logic and module 09's transaction tests).

```python
# Vague: passes for ANY exception, including a typo'd NameError.
with pytest.raises(Exception):
    await service.place_order(...)

# Deliberate: which error, what data, and what state was left behind.
with pytest.raises(InsufficientStockError) as exc:
    await service.place_order(requested_lines=[RequestedLine(1, 100)], ...)
assert exc.value.available == 5
assert (await repo.get(1)).stock_qty == 5        # nothing was reserved
assert gateway.charge_calls == []                # and nobody was charged
```

## Testing behavior, not implementation (again, concretely)

From `01-testing-fundamentals.md`: a good test survives a refactor that preserves
behavior. Concretely, prefer:
- Asserting on `OrderService.place_order()`'s return value and the DB/gateway state
  afterward, over asserting internal call sequences that aren't part of the contract.
- Testing through the same interface real callers use (call `place_order`, not a
  private helper it happens to use this week).
- One meaningful behavioral difference per test, so a failure tells you exactly what
  changed.

## A worked example: designing `test_pricing.py`

Given `calculate_totals(lines, tax_rate)`, a systematic pass looks like:
1. Equivalence classes for subtotal: below all tiers, in each tier.
2. Boundaries: exactly at each tier's threshold, one cent below/above.
3. Multiple lines summing across boundaries (an order with two lines whose combined
   subtotal crosses a threshold that neither line crosses alone).
4. Error paths: empty lines, zero/negative quantity, negative price.
5. A property that should hold for *any* valid input, not just chosen examples:
   `total_cents == subtotal_cents - discount_cents + tax_cents`, always. This is
   exactly what module 12's Hypothesis tests check — the systematic techniques above
   choose good example-based cases; property-based testing checks invariants across
   inputs you'd never think to hand-pick.

## Next

- `04-coverage-and-quality.md` — coverage as a floor, test smells, flakiness
- `modules/02-parametrization` — turning this into runnable pytest
- `modules/12-coverage-and-hypothesis` — property-based testing on `pricing.py`
