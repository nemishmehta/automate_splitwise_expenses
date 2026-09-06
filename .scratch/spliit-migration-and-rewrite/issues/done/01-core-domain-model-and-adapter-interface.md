# 01: Core domain model + adapter interface

**What to build:** Backend-agnostic domain objects for Group, Participant, Expense, Split, and Payer, plus a single `ExpenseBackend` adapter interface (list Groups, list a Group's Participants, list Categories, create an Expense with its Split). Ship an in-memory fake implementation of this interface for tests. No CLI and no real backend connection yet — this is prefactoring that unlocks every later ticket.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Group, Participant, Expense, and Split domain objects/data structures exist, independent of any backend SDK
- [x] Split represents a method (Equal, Exact Amount, or Percentage) plus a per-Participant share, and supports an arbitrary number (2+) of Participants
- [x] A single `ExpenseBackend` adapter interface is defined, covering: list Groups, list a Group's Participants, list Categories, create an Expense (with its Split)
- [x] An in-memory fake implementing `ExpenseBackend` exists, usable by tests
- [x] Unit tests drive the core domain logic against the fake and assert on the Expense+Split payload the fake received
- [x] No I/O (network calls, `input()`/`print()`) appears anywhere in the domain objects

## Implementation notes (agent)

- `src/core/models.py`: frozen dataclasses `Participant`, `Group`, `Category`,
  `Share`, `Split` (with `SplitMethod` enum), `Expense`. `Split.__post_init__`
  enforces 2+ shares and no duplicate Participant. `Expense.split` is
  `Optional[Split]` — `None` for a Personal Expense, present for a Shared
  Expense. Money amounts use `Decimal`, not `float`, to avoid rounding drift
  once exact/percentage splits (issue 06) need to validate sums.
- `src/core/backend.py`: `ExpenseBackend` ABC — `list_groups`,
  `list_participants(group_id)`, `list_categories`, `create_expense(expense)`.
- `src/core/fake_backend.py`: `FakeExpenseBackend` — seeded with Groups and
  Categories at construction; `create_expense` appends to
  `created_expenses` for test assertions.
- Tests: `tests/core/test_models.py`, `tests/core/test_fake_backend.py` (11
  tests total), built test-first per the `/tdd` skill.
- No CLI or Spliit-specific code was touched — this is pure prefactoring, as
  scoped. Issue 02 (Spliit adapter) can now implement `ExpenseBackend`
  directly against these types.
