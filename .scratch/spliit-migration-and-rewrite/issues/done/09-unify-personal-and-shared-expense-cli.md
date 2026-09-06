# 09: Unify Personal and Shared Expense entry into a single CLI flow

**What to build:** Collapse `run_expense_cli.py` (Personal Expenses) and `run_shared_expense_cli.py` (Shared Expenses) into one script and one CLI class covering every Expense type. All Groups — Personal and Shared alike — are sourced from `WhoAmI`'s registered ids (the same registry `SharedExpenseCLI` already uses), and the Group is chosen per-transaction rather than pinned for the whole run via `--group-id`. Once a Group is chosen, its Participant count alone decides whether the transaction is a Personal Expense (1 Participant: no participant-selection or Split-method prompts, submits with `split=None`) or a Shared Expense (2+ Participants: existing choose-Participants/choose-Split flow, unchanged). A run can freely mix Personal and Shared Expenses transaction-by-transaction. See spec.md's "Unify Personal and Shared Expense entry into a single flow" amendment for the full decision set.

**Blocked by:** None (can start immediately) — 02, 05, 07, 08, all already done, are what this unifies.

**Status:** done

- [x] `run_shared_expense_cli.py` is retired; `run_expense_cli.py` is the single entry point for all Expense types, taking only a CSV path (no `--group-id` flag)
- [x] `PersonalExpenseCLI` and `SharedExpenseCLI` are retired in favor of one CLI class in `src/main/expense_cli.py` covering both cases, removing their near-duplicate `run()` loops (transaction iteration, review/skip, Category resolution, submit/confirm)
- [x] The unified flow prompts for which Group a transaction belongs to on every transaction, from the full list of Groups with a registered Payer Configuration (`WhoAmI.known_group_ids()`) — not pinned for the whole run
- [x] Once a Group is chosen for a transaction, exactly 1 Participant skips participant-selection and Split-method prompts and submits a Personal Expense (Payer = that Participant, `split=None`), matching today's `PersonalExpenseCLI._resolve_payer_id` behavior
- [x] Once a Group is chosen for a transaction, 2+ Participants runs the existing Shared Expense flow unchanged (choose Participants, choose Split, Default Split Profile pre-fill)
- [x] No separate "is this Personal or Shared?" question is ever asked — Participant count is the sole signal
- [x] A single run can mix Personal and Shared Expense transactions back to back
- [x] A Personal Expense Group must be registered via `run_configure_who_am_i.py` before it appears in the picker (previously not required); `run_configure_who_am_i.py` itself needs no code change (already works correctly against a 1-Participant Group)
- [x] Core domain objects, the adapter interface, split math, Default Split Profile, and Category Suggestion logic are unchanged — this ticket only touches the CLI wiring layer (`src/main/expense_cli.py` and `src/scripts/`)

## Implementation notes (agent)

- `src/main/expense_cli.py`: `PersonalExpenseCLI` and `SharedExpenseCLI`
  replaced by a single `ExpenseCLI`, constructor identical to the old
  `SharedExpenseCLI`'s (`backend`, `payer_ids`, `csv_path`, plus the
  optional stores). `_registered_groups()` filters `backend.list_groups()`
  down to ids present in `payer_ids` (replaces the old `_shared_groups()`
  participant-count filter). Per transaction, after `_choose_group()`,
  `len(group.participants) == 1` decides `split=None` (Personal) vs. the
  existing choose-Participants/choose-Split path (Shared); the
  submit/confirm block conditionally prints Shares only when `split is not
  None`.
- `src/scripts/run_expense_cli.py`: rewritten to the `WhoAmI`-registry
  wiring `run_shared_expense_cli.py` used (no `--group-id` flag, builds
  `payer_ids` from `who_am_i.known_group_ids()`), now instantiating
  `ExpenseCLI`. `src/scripts/run_shared_expense_cli.py` deleted outright
  (not archived under `obsolete/` — unlike the legacy Splitwise flow, this
  is an in-progress rewrite's internal wiring with no independent value).
- Tests: `tests/main/test_expense_cli.py` rewritten to cover `ExpenseCLI`
  end-to-end (24 tests: personal-expense cases, shared-expense cases
  ported from the old `test_shared_expense_cli.py`, an unregistered-Group
  filtering test, and a new mixed-Personal-and-Shared-in-one-run test).
  `tests/main/test_shared_expense_cli.py` deleted, folded into the above.
- `README.md`'s Phase 2/3 sections updated to match (single
  `run_expense_cli.py` invocation, Personal Expense Groups now require
  registration too).
- All 88 project tests pass; `black`/`flake8`/`isort` clean on every
  touched file (one pre-existing, unrelated `black` finding in
  `src/main/extract_wise_transactions.py` was left alone — out of scope).
