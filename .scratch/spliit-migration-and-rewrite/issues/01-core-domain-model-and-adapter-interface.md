# 01: Core domain model + adapter interface

**What to build:** Backend-agnostic domain objects for Group, Participant, Expense, Split, and Payer, plus a single `ExpenseBackend` adapter interface (list Groups, list a Group's Participants, list Categories, create an Expense with its Split). Ship an in-memory fake implementation of this interface for tests. No CLI and no real backend connection yet — this is prefactoring that unlocks every later ticket.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Group, Participant, Expense, and Split domain objects/data structures exist, independent of any backend SDK
- [ ] Split represents a method (Equal, Exact Amount, or Percentage) plus a per-Participant share, and supports an arbitrary number (2+) of Participants
- [ ] A single `ExpenseBackend` adapter interface is defined, covering: list Groups, list a Group's Participants, list Categories, create an Expense (with its Split)
- [ ] An in-memory fake implementing `ExpenseBackend` exists, usable by tests
- [ ] Unit tests drive the core domain logic against the fake and assert on the Expense+Split payload the fake received
- [ ] No I/O (network calls, `input()`/`print()`) appears anywhere in the domain objects
