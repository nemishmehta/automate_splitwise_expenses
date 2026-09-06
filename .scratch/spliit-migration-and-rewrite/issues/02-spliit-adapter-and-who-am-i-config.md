# 02: Spliit adapter + per-Group "who am I" configuration

**What to build:** A real implementation of the `ExpenseBackend` adapter interface against Spliit's hosted instance (spliit.app), using Spliit's existing Python client library. Since Spliit has no login/account concept, add a one-time per-Group configuration step that records which Participant is you, so the adapter knows whose Paid Share to fill in as the Payer.

**Blocked by:** 01 (core domain model + adapter interface)

**Status:** in-progress (adapter + who-am-i config implemented and tested; real-Spliit visibility check is a manual/HITL step)

- [x] The adapter implements list Groups, list a Group's Participants, list Categories, and create an Expense against the real Spliit hosted instance
- [x] A configuration mechanism exists to record which Participant is "you" (the **Payer Configuration**, see `CONTEXT.md`) for each Group, set once and reused on subsequent runs without re-asking
- [ ] Creating an Expense through this adapter results in a real Expense visible in the corresponding Spliit Group
- [x] Existing Splitwise Groups, Participants, and expense history are left untouched by this work

## Design decisions (resolved pre-implementation, see [ADR 0002](../../../docs/adr/0002-spliit-client-dependency-and-payer-identity.md))

- **Client dependency**: no official Spliit Python client exists (ADR 0001's claim to the contrary was wrong). Depend on the unofficial PyPI package `spliit-api-client`, pinned to an exact version (not a caret range) in `pyproject.toml`.
- **Payer Configuration placement**: kept out of the `ExpenseBackend` interface entirely — it's a Spliit-specific quirk (no login), not something every backend needs. Implement it as its own component alongside the adapter (e.g. `src/spliit/who_am_i.py`), not in `src/core`.
- **Payer Configuration storage**: a JSON file behind a small class, `{group_id: participant_id}`, matching the precedent in `src/core/category_suggestion.py`'s `CategorySuggestionHistory`.
- **Payer Configuration trigger**: a separate, explicit one-time setup script (e.g. `src/scripts/run_configure_who_am_i.py`) run once per new Group — not an inline prompt woven into the not-yet-built CLI (issue 03). This makes issue 02 independently demoable.
- **Adapter location**: lives in its own module (e.g. `src/spliit/backend.py`), not `src/core`, since it does real I/O and depends on a third-party package — `src/core` stays I/O-free per issue 01's decisions.
- **Testing**: automated tests mock the `spliit-api-client` boundary, no real network calls in the suite. "Results in a real Expense visible in Spliit" is a manual, one-time verification step against an existing real Spliit Group (already set up, owned by the tool's operator) — not an automated test.
- **Superseded during implementation, see ADR 0002's Amendment**: `spliit-api-client` turned out to be unusable at every published version (0.1.2-0.1.5 ship empty wheels; 0.1.0/0.1.1 crash on import under this project's Python 3.9 due to a `datetime.UTC` reference that only exists in Python 3.11+). No PyPI dependency was added; a small local client was vendored instead (`src/spliit/client.py`).

## Implementation notes (agent)

- `src/spliit/client.py`: `SpliitClient` (dataclass, `group_id` + `base_url`)
  and `SplitMode` enum (`EVENLY`/`BY_SHARES`/`BY_PERCENTAGE`/`BY_AMOUNT`) —
  a vendored, Python-3.9-safe port of the two operations this tool needs
  from `spliit-api-client` 0.1.1's working code (`get_group`,
  `add_expense`), calling Spliit's undocumented tRPC endpoints directly via
  `requests`. See ADR 0002's Amendment for why this exists instead of a
  PyPI dependency.
- `src/spliit/backend.py`: `SpliitExpenseBackend(ExpenseBackend)`.
  Constructor takes `group_ids: Iterable[str]` — Spliit has no "list my
  groups" API (no login concept), so the caller supplies which Group ids
  exist; this adapter's job is to fetch/wrap them, not discover them.
  `list_categories()` returns a hardcoded `Category` tuple mirroring
  Spliit's fixed, client-side-only category taxonomy (no live endpoint
  exists for this either). `create_expense`: a Personal Expense
  (`expense.split is None`) submits as an even split of one
  (`paid_for=[payer_id]`); a Shared Expense submits every
  `Split.share`'s exact owed amount (payer included — `compute_equal_split`
  already assigns the payer a Share too) via `split_mode=BY_AMOUNT`,
  regardless of the original `SplitMethod` (Equal/Exact/Percentage), since
  the core has already computed exact amounts and `BY_AMOUNT` is the one
  Spliit mode that reflects an already-computed split unambiguously.
  Amounts are converted from `Decimal` euros to integer cents.
- `src/spliit/who_am_i.py`: `WhoAmI`, a JSON-file-backed
  `{group_id: participant_id}` store, structurally identical to
  `CategorySuggestionHistory` (`get`/`set` instead of `get`/`record`).
- `src/scripts/run_configure_who_am_i.py`: one-time setup script
  (`--group-id`), lists the Group's Participants, prompts for which one is
  you, saves via `WhoAmI`. Writes to `who_am_i.json` at the repo root
  (added to `.gitignore` — local per-operator config, not committed).
- Tests: `tests/spliit/test_backend.py` (5 tests, mocking
  `src.spliit.backend.SpliitClient`) and `tests/spliit/test_who_am_i.py`
  (5 tests, real JSON file via `tmp_path`, mirroring
  `test_category_suggestion.py`'s store tests) — no real network calls.
- **Remaining/deferred**: the "results in a real Expense visible in
  Spliit" box is an explicit manual/HITL verification step per the ADR's
  own testing decision — it needs the owner's real, already-configured
  Spliit Group and isn't something an AFK agent can check off. Everything
  else in this issue's scope is done.
