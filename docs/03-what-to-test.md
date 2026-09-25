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

## Boundary value analysis

Bugs cluster at the edges of partitions (off-by-one errors, `<` vs `<=`), so test
*at* and *adjacent to* every boundary, not just comfortably inside each partition.
For a threshold at 5,000 cents: test 4,999, 5,000, and 5,001 — three cases, not one,
and specifically the three most likely to catch a real mistake.

## Decision tables

When behavior depends on a *combination* of independent conditions, list every
combination in a table and derive one test per row (or per row that matters — a full
table can be pruned once you understand which combinations are actually reachable
or actually distinct in outcome). `OrderService.place_order`'s error handling is a
decision-table problem: {product exists?} x {stock sufficient?} x {payment
succeeds?} x {idempotency key already used?} each independently flips the outcome.

## State transition testing

For anything with a lifecycle — `OrderStatus`: `pending -> paid -> refunded`, or
`pending -> cancelled` — enumerate the valid transitions *and* explicitly test the
invalid ones (can you cancel an already-refunded order? Can you pay a cancelled
one?). `InvalidOrderStateError` in this repo exists specifically to make illegal
transitions a tested, intentional error rather than an accident of whatever the code
happens to do. Draw the state diagram before writing the tests if it isn't obvious.

## Error paths, deliberately, not incidentally

It's easy to write ten tests for the happy path and one vague `pytest.raises`
catch-all for "errors." Treat each distinct failure mode as its own first-class case
with its own assertion on *which* exception and *what* the system state is
afterward (did a partial write happen? was stock released? see
`services/orders.py`'s compensation logic and module 09's transaction tests).

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
