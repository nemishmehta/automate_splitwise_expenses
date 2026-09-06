# 06: Shared Expense — Exact Amount and Percentage splits across N Participants

**What to build:** Let the owner split a Shared Expense by exact amount or by percentage across the chosen 2+ Participants, validating that entered shares sum to the Expense total (Exact Amount) or 100% (Percentage), within a small rounding tolerance, before the Split is accepted.

**Blocked by:** 05 (Shared Expense — Equal split across N Participants)

**Status:** in-progress (core split computation + validation done; CLI selection deferred, same as 05)

- [ ] Owner can choose Exact Amount as the split method and enter an amount for each non-Payer Participant
- [x] An Exact Amount split is rejected, with a re-prompt, if entered shares don't sum to the Expense total (within a small rounding tolerance)
- [ ] Owner can choose Percentage as the split method and enter a percentage for each non-Payer Participant
- [x] A Percentage split is rejected, with a re-prompt, if entered percentages don't sum to 100% (within a small rounding tolerance)
- [x] Both methods work for exactly 2 Participants and for 3 or more Participants

## Implementation notes (agent)

- `src/core/split.py`: two new pure functions alongside `compute_equal_split`:
  - `compute_exact_split(amounts: Mapping[str, Decimal], total, payer_id) -> Split`
    — builds a Split directly from the given per-Participant amounts (payer
    included, mirroring `compute_equal_split`'s signature style of taking
    every participant rather than "non-payer only"). Raises `ValueError` if
    `payer_id` isn't among the given amounts, or if the amounts don't sum
    to `total` within `_TOLERANCE` (`Decimal("0.01")`). Unlike Equal/
    Percentage, no remainder is force-assigned to the payer here: the
    amounts are the owner's own explicit entries, not tool-computed, so
    they're taken as-is once validated (can differ from `total` by up to
    the tolerance).
  - `compute_percentage_split(percentages: Mapping[str, Decimal], total, payer_id) -> Split`
    — same validation shape (`ValueError` if payer missing, or if
    percentages don't sum to 100 within `_TOLERANCE`), then converts each
    percentage to a cent-rounded amount (`ROUND_DOWN`) and — like
    `compute_equal_split` — assigns the rounding remainder to the payer's
    Share so the Shares always sum exactly back to `total` regardless of
    percentage-input slop.
  - Module-level `_TOLERANCE = Decimal("0.01")`, alongside the existing `_CENT`.
- Tests: `tests/core/test_split.py` grew from 6 to 19 tests — for each of
  Exact/Percentage: 2-participant and 3+-participant cases, the
  sum-validation rejection, an accept-within-tolerance case, the
  payer-not-included rejection, and one `FakeExpenseBackend` submission
  test (mirroring the existing Equal-split integration test). Percentage
  additionally has a rounding-remainder-to-payer test analogous to Equal's.
- **Design decision made without a HITL round-trip:** whether the Exact
  Amount API takes amounts for all Participants (including payer) or only
  non-payer ones (with the payer's share derived as the remainder) was
  ambiguous between the issue's checklist wording ("enter an amount for
  each non-Payer Participant") and its validation wording ("if entered
  shares don't sum to the Expense total"). Went with "all Participants,
  including payer" for symmetry with `compute_equal_split` and because
  it's the simpler, most directly testable core seam; the not-yet-built
  CLI is free to collect non-payer amounts and derive/pre-fill the payer's
  as `total - sum(others)` before calling this function — that's a CLI
  concern, not a core one.
- **Remaining/deferred, same reasoning as issue 05:** the two "Owner can
  choose ... and enter ..." checkboxes are CLI-facing selection/entry UI.
  No Shared Expense CLI flow exists yet at all (`src/main/expense_cli.py`
  only handles Personal Expenses) — building and verifying one needs
  issue 02/03's real-Spliit-group HITL step, same blocker already recorded
  on issue 05. Once that CLI exists, wire `compute_exact_split` and
  `compute_percentage_split` in alongside `compute_equal_split` as the
  other two split-method options and check off the remaining boxes.
