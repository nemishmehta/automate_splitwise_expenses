# 02: Spliit adapter + per-Group "who am I" configuration

**What to build:** A real implementation of the `ExpenseBackend` adapter interface against Spliit's hosted instance (spliit.app), using Spliit's existing Python client library. Since Spliit has no login/account concept, add a one-time per-Group configuration step that records which Participant is you, so the adapter knows whose Paid Share to fill in as the Payer.

**Blocked by:** 01 (core domain model + adapter interface)

**Status:** ready-for-agent

- [ ] The adapter implements list Groups, list a Group's Participants, list Categories, and create an Expense against the real Spliit hosted instance
- [ ] A configuration mechanism exists to record which Participant is "you" (the **Payer Configuration**, see `CONTEXT.md`) for each Group, set once and reused on subsequent runs without re-asking
- [ ] Creating an Expense through this adapter results in a real Expense visible in the corresponding Spliit Group
- [ ] Existing Splitwise Groups, Participants, and expense history are left untouched by this work

## Design decisions (resolved pre-implementation, see [ADR 0002](../../../docs/adr/0002-spliit-client-dependency-and-payer-identity.md))

- **Client dependency**: no official Spliit Python client exists (ADR 0001's claim to the contrary was wrong). Depend on the unofficial PyPI package `spliit-api-client`, pinned to an exact version (not a caret range) in `pyproject.toml`.
- **Payer Configuration placement**: kept out of the `ExpenseBackend` interface entirely — it's a Spliit-specific quirk (no login), not something every backend needs. Implement it as its own component alongside the adapter (e.g. `src/spliit/who_am_i.py`), not in `src/core`.
- **Payer Configuration storage**: a JSON file behind a small class, `{group_id: participant_id}`, matching the precedent in `src/core/category_suggestion.py`'s `CategorySuggestionHistory`.
- **Payer Configuration trigger**: a separate, explicit one-time setup script (e.g. `src/scripts/run_configure_who_am_i.py`) run once per new Group — not an inline prompt woven into the not-yet-built CLI (issue 03). This makes issue 02 independently demoable.
- **Adapter location**: lives in its own module (e.g. `src/spliit/backend.py`), not `src/core`, since it does real I/O and depends on a third-party package — `src/core` stays I/O-free per issue 01's decisions.
- **Testing**: automated tests mock the `spliit-api-client` boundary, no real network calls in the suite. "Results in a real Expense visible in Spliit" is a manual, one-time verification step against an existing real Spliit Group (already set up, owned by the tool's operator) — not an automated test.
