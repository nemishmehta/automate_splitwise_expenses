# 06: Shared Expense — Exact Amount and Percentage splits across N Participants

**What to build:** Let the owner split a Shared Expense by exact amount or by percentage across the chosen 2+ Participants, validating that entered shares sum to the Expense total (Exact Amount) or 100% (Percentage), within a small rounding tolerance, before the Split is accepted.

**Blocked by:** 05 (Shared Expense — Equal split across N Participants)

**Status:** complete

- [x] Owner can choose Exact Amount as the split method and enter an amount for each non-Payer Participant
- [x] An Exact Amount split is rejected, with a re-prompt, if entered shares don't sum to the Expense total (within a small rounding tolerance)
- [x] Owner can choose Percentage as the split method and enter a percentage for each non-Payer Participant
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

## CLI wiring (agent, follow-up session)

Issue 05's Shared Expense CLI flow (`SharedExpenseCLI` in
`src/main/expense_cli.py`) landed after the note above was written, and is
fully testable against `FakeExpenseBackend` with no real Spliit group
needed — the "needs a real-Spliit HITL step" reasoning above turned out to
apply only to the adapter's own visibility check (issue 02), not to this
CLI wiring. Completed the two remaining checkboxes on that basis:

- `SharedExpenseCLI._choose_split` (new): prompts for a split method
  (Equal / Exact Amount / Percentage) after participant selection, for all
  `participant_ids` (payer included, mirroring `compute_equal_split`'s
  signature and issue 06's earlier "all Participants, including payer"
  decision). Equal calls `compute_equal_split` directly (unchanged
  behavior, now behind an explicit method choice instead of being the only
  option).
- `SharedExpenseCLI._prompt_split` (new): shared re-prompt loop for Exact
  Amount and Percentage. Lists the chosen Participants by name, then reads
  one comma-separated line of values in that same order, builds a
  `{participant_id: Decimal}` mapping, and calls the given core split
  function. Catches `ValueError` (bad sum, from the core) and
  `decimal.InvalidOperation` (unparseable input) alike, prints the error,
  and re-prompts on the same line rather than restarting the whole
  transaction.
- Tests: `tests/main/test_shared_expense_cli.py` grew from 7 to 11 tests —
  added Exact Amount and Percentage happy-path tests plus one re-prompt
  test per method (bad sum on the first attempt, valid on the second). The
  7 existing tests were updated in place to add the new split-method-choice
  input ("1" for Equal) at the point in their input sequence where it now
  occurs — an intentional interface change (a new required prompt), not a
  behavior regression; all now pass alongside the new tests.
- No changes to `src/core/split.py` — both functions were already correct
  and fully covered from the prior session's work on this issue.
- Full suite (`poetry run pytest`) is green at 102 tests; `flake8` and
  `isort` clean; `black` reformatted `expense_cli.py` (pre-existing
  unrelated `black` diff in `extract_wise_transactions.py` left untouched,
  out of scope for this issue).
