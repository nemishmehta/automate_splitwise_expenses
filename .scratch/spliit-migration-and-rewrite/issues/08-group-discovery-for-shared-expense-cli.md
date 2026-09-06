# 08: Group Discovery for Shared Expense CLI (no upfront --group-id)

**What to build:** Replace `run_shared_expense_cli.py`'s required, repeatable `--group-id` argument with automatic discovery of every Group that already has a Payer Configuration, so the owner never has to know or paste a Group id to start a Shared Expense run — matching the "list Groups, then pick one" shape of the old Splitwise flow, adapted to Spliit's no-login constraint (see spec.md's Amendment for issue 08).

**Blocked by:** 02 (Spliit adapter + who-am-i config), 05 (Shared Expense Group/Participant selection UI) — both already done; this issue only touches wiring around them, not their UI.

**Status:** ready-for-agent

- [ ] `run_shared_expense_cli.py` runs without any `--group-id` argument; the only positional argument is the CSV path
- [ ] The existing Group picker (`SharedExpenseCLI`'s `_choose_group`) offers every Group that has a Payer Configuration recorded, and no Group that doesn't
- [ ] Registering a brand-new Group still requires pasting its id once into `run_configure_who_am_i.py --group-id` (unchanged) — after that one-time step it appears in the picker on every future `run_shared_expense_cli.py` run without repeating the id
- [ ] If zero Groups have a Payer Configuration yet, the run stops before processing any transactions with a clear message pointing at `run_configure_who_am_i.py`, instead of failing deep inside the CLI
- [ ] If fetching a specific registered Group from Spliit fails (deleted Group, network error), that one Group is skipped with a warning and the run continues with the remaining Groups, rather than aborting the entire run
- [ ] Existing per-transaction Group/Participant/Split selection behavior (`SharedExpenseCLI`) is unchanged

## Design decisions (resolved pre-implementation, via grilling)

- **No live "list my Groups" capability exists or is being added.** Confirmed Spliit has no login/account concept and no such endpoint — the Spliit client only supports fetching one Group by an id the caller already has (see ADR 0002). Splitwise's `getGroups()` has no Spliit equivalent, and this issue does not attempt to add one (there is no undocumented endpoint known to exist for it).
- **Registry of "known" Groups = the existing Payer Configuration store, not a new file.** Every Group usable by `SharedExpenseCLI` already requires a Payer Configuration entry — the CLI looks up the Payer by Group id with no missing-key guard — so a Group without one can't be used regardless of what discovers it. Reusing the Payer Configuration store's own keys as the registry avoids introducing a second store that could drift out of sync with it.
  - Rejected: a separate `group_id -> name` registry file, independent of Payer Configuration — two stores that must be kept in sync for no added benefit.
  - Rejected: keeping `--group-id` as an optional filter flag on top of discovery — duplicates what the interactive picker already does; a single-Group session can just pick that one Group in the prompt.
- **Registration stays a separate, explicit step.** `run_configure_who_am_i.py` (paste a Group id once, choose your Payer) remains the only way to add a Group to the picker. `run_shared_expense_cli.py` never accepts a raw Group id.
  - Rejected/deferred: an inline "add a new Group by id" option inside the picker itself. Keeps "register a Group" and "use a Group" as one job each, matching the existing setup/use split established in issue 02. Can be revisited later if pasting an id mid-run turns out to be worth the added surface.
- **The current missing-payer validation in `run_shared_expense_cli.py` becomes unreachable and should be removed, not kept as dead code.** It exists today to check each requested `--group-id` for a configured Payer; once the Group list itself comes from the Payer Configuration store's own keys, every discovered Group has a Payer by construction.
- **Per-Group fetch resilience is Spliit-adapter-specific, not a core/interface change.** A fetch failure for one registered Group (deleted Group, network error) is caught and that Group is skipped with a warning, rather than the whole run aborting. This should be added as adapter-level behavior (e.g. an optional error-reporting hook on the Spliit adapter), not a change to the backend-agnostic adapter interface — the same reasoning ADR 0002 used to keep Payer Configuration off that interface applies here (it's a quirk of Spliit's undocumented, failure-prone API, not something every backend needs).
- **Empty-picker guard.** If the Payer Configuration store has zero entries, or every registered Group fails to fetch, the run stops with a clear message before entering the transaction-review loop, rather than reaching an empty picker mid-loop.
- **Scope boundary:** `run_expense_cli.py` (Personal Expense CLI) is unaffected. It always operates on exactly one fixed Group (the owner's own Personal Expense Group) with no "pick from a list" step to begin with, so the `--group-id` it requires is a different, unrelated case and is out of scope for this issue.
