# 05: Shared Expense — Equal split across N Participants

**What to build:** Let the owner choose a Group (other than a Personal Expense group) and a subset of 2 or more of its Participants (not necessarily the whole Group), and split an Expense equally among the chosen set as a Shared Expense. This establishes the Group/Participant-subset selection UI that later split-method tickets reuse.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** done

- [x] Owner can choose a Group (other than a Personal Expense group) for a transaction
- [x] Owner can choose a subset of 2+ Participants from that Group's members to share the Expense — the full Group is not required
- [x] An Equal split divides the Expense's total across the chosen Participants, with any rounding remainder assigned deterministically (e.g. to the Payer)
- [x] The Expense+Split submitted through the adapter correctly reflects the Payer's paid share and each Participant's owed share
- [x] Works for exactly 2 Participants and for 3 or more Participants

## Implementation notes (agent)

- `src/core/split.py`: pure `compute_equal_split(participant_ids, total,
  payer_id) -> Split`. Divides `total` by participant count, rounds each
  Share down to the cent (`ROUND_DOWN`), then adds the leftover remainder
  to the Payer's Share so Shares always sum exactly back to `total`.
  Raises `ValueError` if `payer_id` isn't among `participant_ids`
  (the <2-participants case is already covered by `Split.__post_init__`
  from issue 01, so no separate check was needed for that).
- Tests: `tests/core/test_split.py` (6 tests) — 2-participant even split,
  3-participant even split, 3-participant split with a rounding remainder
  (10 / 3, remainder assigned to Payer), both error cases, and one
  integration-style test building an `Expense` with the computed `Split`
  and submitting it through `FakeExpenseBackend`, asserting on what the
  fake received (per spec.md's Testing Decisions).
- This computation function is the reusable seam issues 06 (Exact/
  Percentage) and 07 (Default Split Profile) can build alongside, per the
  ticket's own note that 05 "establishes... later split-method tickets
  reuse."

## Implementation notes (agent, CLI wiring — final pass)

- **Re-evaluated the prior "blocked on HITL/real Spliit" note and found it
  wrong**: the remaining two checkboxes (Group choice, Participant-subset
  choice) are CLI selection UI, and issue 03's own closing notes already
  said this was "now unblocked since this CLI exists" — no real Spliit
  Group is needed to build or test it, only `FakeExpenseBackend`, exactly
  like `PersonalExpenseCLI`'s existing tests. A prior iteration's notes on
  this issue (and 04/06) mis-recorded this as HITL-blocked; corrected here.
- `src/main/expense_cli.py`: added `SharedExpenseCLI`, mirroring
  `PersonalExpenseCLI`'s shape (constructor takes an `ExpenseBackend`, the
  CSV path, injectable `input_fn`/`print_fn`). Differences from
  `PersonalExpenseCLI`:
  - Takes `payer_ids: Mapping[str, str]` (group_id -> Payer's
    participant_id) instead of a single `group_id`, since a Shared Expense
    run may offer multiple candidate Groups and each needs its own Payer
    Configuration (issue 02's `WhoAmI`) — kept out of `src/main` to stay
    backend-agnostic; the script resolves `WhoAmI` lookups into this dict
    before constructing the CLI.
  - `_shared_groups()`: filters `backend.list_groups()` to Groups with 2+
    Participants, which is exactly the definition of "not a Personal
    Expense Group" already established in `PersonalExpenseCLI` — reused
    that definition rather than inventing a separate flag.
  - `_choose_group()` / `_choose_participants()`: print a numbered list,
    take a 1-based index (or comma-separated indices for participants).
    The Payer is resolved first via `payer_ids[group.id]` and excluded
    from the participant-choice list (owner picks who *else* shares the
    Expense); final `participant_ids` passed to `compute_equal_split` is
    `[payer_id] + chosen_others`. This resolves the ambiguity noted in
    issue 06 the same way issue 06 itself resolved it: the payer is always
    part of the Split.
  - `category_id=None` still hardcoded (issue 04's pre-fill is separate,
    already unblocked by this same CLI existing).
- `src/scripts/run_shared_expense_cli.py`: entry point (repeatable
  `--group-id`, `csv_path`), resolves each Group's Payer via `WhoAmI`
  (erroring out with a clear message if any Group has no Payer
  Configuration yet), wires a real `SpliitExpenseBackend` to
  `SharedExpenseCLI`.
- Tests: `tests/main/test_shared_expense_cli.py` (7 tests, built test-first
  per `/tdd`, against `FakeExpenseBackend` with injected input/print
  functions, no real network) — happy path with 3 Participants, exactly-2-
  Participants case, Personal Expense Groups excluded from the Group
  choice list, skip-before-group-choice, cancel-at-confirmation, backend
  error message, and summary counts. Mirrors `test_expense_cli.py`'s
  existing coverage shape for `PersonalExpenseCLI`.
- **Manual/HITL still deferred, same as issues 02/03's precedent**: running
  `run_shared_expense_cli.py` against a real, already-configured Spliit
  Group with 2+ Participants and confirming the Expense actually appears
  in Spliit (with correct Shares) is a manual verification step for the
  tool's owner, not an automated test.
- **Next**: issue 06's remaining CLI-wiring checkboxes (Exact
  Amount/Percentage as alternate split methods in this same flow) and
  issue 04's Category Suggestion pre-fill are both now buildable the same
  way (no HITL blocker) — good candidates for the next AFK iteration.
