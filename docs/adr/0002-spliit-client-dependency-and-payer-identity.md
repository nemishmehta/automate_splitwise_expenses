---
status: accepted
---

# Spliit client dependency, and Payer identity kept outside the backend interface

ADR 0001 assumed Spliit had "an existing Python client library" as one reason to
choose it. That claim was never verified. Research for issue 02 found no
official client: only two small, unofficial, reverse-engineered wrappers exist
on PyPI, both calling Spliit's undocumented tRPC backend (Spliit exposes no
documented REST/GraphQL API). Separately, since Spliit has no login concept,
something has to record which Participant is the Payer for each Group.

## Considered Options — Spliit connectivity

- **`spliit-api-client`** (chosen): PyPI package, fork of `guysoft/SpliitApi`,
  most recently active of the two unofficial options (released 2025-02-11).
  Covers listing groups/participants/categories and creating an expense with a
  split mode and payer — the operations `ExpenseBackend` needs.
- **`spliit-client`**: newer (2025-07-02) but zero GitHub stars/traction; its
  own README states it is unofficial and unaffiliated with Spliit. No
  advantage over `spliit-api-client` beyond being newer.
- **Hand-rolled tRPC wrapper** (rejected): calling Spliit's tRPC endpoints
  directly would remove the dependency-freshness risk entirely, but re-does
  reverse-engineering work two other people have already done, for a personal
  tool where that risk is low-stakes. Not worth the effort.

## Considered Options — Payer identity placement

- **New abstract methods on `ExpenseBackend`** (e.g. `get_payer_id` /
  `set_payer_id`) (rejected): Payer identity only needs manual configuration
  because Spliit specifically has no login/account concept. A hypothetical
  future backend with real accounts wouldn't need this at all, so putting it
  on the generic adapter interface would leak a Spliit-specific quirk into
  the backend-agnostic surface every adapter must implement.
- **Standalone component outside `ExpenseBackend`** (chosen): a small
  JSON-file-backed store, keyed `group_id -> participant_id`, matching the
  precedent set by `CategorySuggestionHistory`
  (`src/core/category_suggestion.py`). Resolved once per Group via a separate
  one-time setup script, not asked per Expense, and not part of the
  `ExpenseBackend` interface.

## Consequences

- Depending on `spliit-api-client` ties this tool to an externally
  maintained, low-traction package (a handful of GitHub stars, single
  maintainer) wrapping Spliit's undocumented tRPC API. Pin the exact version
  in `pyproject.toml` rather than a caret range — a point release from a
  package this small is more likely to be an accidental breaking change than
  a considered semver bump. If Spliit's backend shape changes and breaks it,
  expect to patch or replace the dependency, not to have advance warning.
- The Spliit adapter and its Payer-identity store are Spliit-specific
  plumbing and live alongside the adapter (not in `src/core`), keeping the
  backend-agnostic core free of I/O and free of this backend's quirks, per
  the existing "no I/O in domain objects" rule.

## Amendment (issue 02 implementation): `spliit-api-client` is unusable, vendored a local client instead

Implementing against the chosen `spliit-api-client` dependency, two further
problems surfaced that make the "Spliit connectivity" decision above void in
practice:

1. **Every version from 0.1.2 through 0.1.5 (the version this ADR
   originally said to pin) ships an empty wheel.** Downloading and
   inspecting each wheel directly (`pip download --no-deps
   spliit-api-client==<version>`) shows 0.1.2, 0.1.3, 0.1.4, and 0.1.5
   contain only `dist-info` metadata — no `spliit/` package, no code at
   all. Only 0.1.0 and 0.1.1 actually ship the `spliit` module.
2. **0.1.0 and 0.1.1 both crash on import under Python 3.9** — the
   project's pinned interpreter (`python = "^3.9"` in `pyproject.toml`,
   confirmed against the project's actual poetry venv, Python 3.9.16).
   Both versions' `spliit/__init__.py` and `spliit/utils.py`
   unconditionally do `from datetime import datetime, UTC`;
   `datetime.UTC` was only added in Python 3.11, so `from spliit.client
   import Spliit` raises `ImportError` before any of our code even runs.

Combined, no published version of `spliit-api-client` is usable by this
project. This invalidates the "Hand-rolled tRPC wrapper" rejection above —
its stated reason for rejection ("re-does reverse-engineering work two
other people have already done") no longer holds, because that existing
work is not actually usable here.

**Decision (revised):** vendor a small local client,
`src/spliit/client.py` (`SpliitClient`, `SplitMode`), covering only the two
operations this tool needs — `get_group()` and `add_expense(...)` — as a
Python 3.9-safe port of 0.1.1's working logic (`timezone.utc` in place of
the unavailable `datetime.UTC`), calling Spliit's undocumented tRPC
endpoints directly via `requests`. No PyPI dependency on `spliit-api-client`
is added to `pyproject.toml`.

- **Consequence**: this tool now owns reverse-engineering upkeep for
  Spliit's tRPC shape directly, rather than inheriting it from (and being
  blocked by) a third-party package. For a personal tool with a tiny used
  surface (two calls), this is less risk than depending on a package that,
  as observed, can silently ship empty releases.
- Tests still mock at the client boundary (now `src/spliit.client.SpliitClient`
  instead of the external package) — no real network calls in the suite,
  per this ADR's original testing decision.
