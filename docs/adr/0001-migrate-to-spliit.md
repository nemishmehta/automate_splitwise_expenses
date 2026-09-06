---
status: accepted
---

# Migrate from Splitwise to Spliit, behind a backend-agnostic core

Splitwise introduced API pricing, forcing a move to an open-source expense-sharing backend. We evaluated Spliit, IHateMoney, and Cospend (Nextcloud) and chose **Spliit**, accessed through the free hosted instance at spliit.app, sitting behind a backend-agnostic core (Group/Participant/Expense/Split as domain objects with an adapter underneath) rather than a hard swap straight to Spliit's API.

## Considered Options

- **Cospend (Nextcloud app)**: the only alternative that preserves Splitwise's login-based identity model, but it requires standing up and maintaining a Nextcloud instance just to keep that property — too much operational cost for a personal tool, where manually configuring "who am I" per Group once is an acceptable trade-off instead.
- **IHateMoney**: has a documented REST API and multi-currency support, but its bill API has no category field, and this project relies on per-expense categorization.
- **Spliit** (chosen): free hosted instance, per-expense categories, multi-currency, split modes that map directly onto Equal/Exact/Percentage, and an existing Python client library.
- **Hard swap directly to Spliit's API, no abstraction layer**: rejected because the N-person split rewrite and the new UI were happening at the same time regardless of backend choice, and both want a backend-agnostic core — building the adapter now is nearly free relative to doing it later, once CLI and UI both depend directly on Spliit-specific calls.

## Consequences

- Spliit has no accounts, so "who am I" in each Group must be configured manually rather than derived from a login.
- Existing Splitwise groups and expense history are not migrated; they remain in Splitwise, read-only, and only new expenses go through this tool from now on.
