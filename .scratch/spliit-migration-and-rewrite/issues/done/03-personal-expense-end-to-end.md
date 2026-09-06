# 03: End-to-end Personal Expense flow via the new CLI

**What to build:** Rewrite the CLI as a thin interface layer over the core. It reads the cleaned CSV, presents each transaction for review, lets the owner submit a transaction as a Personal Expense (a Group containing only themself), shows a success/error message per submission, and prints a summary once all transactions have been processed. This is the first fully demoable end-to-end slice, run against real Spliit.

**Blocked by:** 01 (core domain model + adapter interface), 02 (Spliit adapter + who am I configuration)

**Status:** done

- [x] CLI reads a cleaned CSV (date, amount, description, currency) and presents each transaction for review, one at a time
- [x] Owner can skip a transaction without uploading it
- [x] Owner can choose to submit a transaction as a Personal Expense against a Group containing only themself
- [x] Collected details are shown for confirmation before the Expense is actually submitted
- [x] A clear success or error message appears after each submission attempt
- [x] A summary is shown once all reviewed transactions have been processed
- [x] The CLI contains no business logic (e.g. split validity, Expense construction) — it only gathers input and calls the core

## Implementation notes (agent)

- `src/core/transactions.py`: `Transaction` (frozen dataclass: `date`,
  `amount: Decimal`, `description`, `currency`) plus `parse_transaction_row`
  (pure, one CSV row dict -> `Transaction`) and `read_transactions_csv`
  (opens the cleaned CSV, semicolon-delimited per `clean_csv.py`'s output,
  and maps each row through the parser). Lives in `src/core` alongside
  `CategorySuggestionHistory`/`WhoAmI` (small file-reading components, not
  domain objects) rather than in the CLI, since parsing/typing a row
  (date/Decimal conversion) is data-shaping the CLI shouldn't own.
- `src/main/expense_cli.py`: `PersonalExpenseCLI` — the thin interface
  layer. Constructor takes an `ExpenseBackend`, the Personal Expense
  Group's id, the CSV path, and injectable `input_fn`/`print_fn` (default
  `input`/`print`) so the review loop is testable without real stdio.
  `run()`: resolves the Payer as the Group's sole Participant (a Personal
  Expense Group is defined as containing only the owner, so no per-Expense
  "who am I" prompt is needed — issue 02's Payer Configuration is only for
  multi-Participant Groups), reads the transactions, then per transaction:
  print details -> Enter-to-review/any-key-to-skip -> print confirmation
  -> Enter-to-submit/any-key-to-cancel -> build an `Expense`
  (`category_id=None`, `split=None` - Category Suggestion (issue 04) and
  Shared Expense splits (issues 05-07) are out of this issue's scope) and
  call `backend.create_expense`, printing success or the caught
  exception's message on failure. Prints a running-total summary line
  (submitted/skipped/failed/total) after the last transaction. No split
  validity, category resolution, or Expense-construction *decisions* live
  here beyond assembling the dataclass from already-typed fields, matching
  the "CLI contains no business logic" requirement.
- `src/scripts/run_expense_cli.py`: entry point (`--group-id`,
  `csv_path`), wires a real `SpliitExpenseBackend` to `PersonalExpenseCLI`,
  mirroring `run_configure_who_am_i.py`'s script shape.
- Tests: `tests/core/test_transactions.py` (2 tests: row parsing, real-file
  reading via `tmp_path`) and `tests/main/test_expense_cli.py` (6 tests,
  built test-first per `/tdd`, against `FakeExpenseBackend` with injected
  input/print functions) — covers submit, skip-before-confirmation,
  cancel-at-confirmation, success message, error message (a `FakeExpenseBackend`
  subclass whose `create_expense` raises), and summary counts. No test
  asserts on prompt wording/internal call order, per the CLI testing
  decision in spec.md.
- **Deferred/out of scope for this issue, left for their own tickets**:
  Category Suggestion pre-fill (issue 04) and Shared Expense Group/split
  selection (issues 05-07) are not wired into `PersonalExpenseCLI` yet —
  `category_id` and `split` are hardcoded to `None`/`None`. Wiring those in
  is each ticket's own remaining checkbox, now unblocked since this CLI
  exists.
- **Manual/HITL verification** (per this issue's own intro: "run against
  real Spliit"): running `run_expense_cli.py` against a real, already
  configured Spliit Personal Expense Group and confirming the Expense
  actually appears in Spliit is a manual step for the tool's owner, not an
  automated test - consistent with issue 02's precedent for real-Spliit
  visibility checks.
