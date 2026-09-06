Status: ready-for-agent

# Migrate to Spliit and rework expense entry (N-person splits, default split profiles, category suggestions, backend-agnostic core)

## Problem Statement

Splitwise has introduced pricing for API access, which this tool depends on entirely for uploading expenses — the tool cannot keep working against Splitwise's API for free. Separately, even before that forcing event, the tool had accumulated friction in daily use:

- A Shared Expense can currently only be split between exactly two Participants (yourself and one other), even though real expenses are sometimes shared across a larger Group.
- The same Split (method + shares) against the same other person or people is re-entered by hand on every single Expense, even when it's virtually always the same — most often a fixed percentage split with one specific other person.
- The tool is CLI-only, which is fine for the owner but forecloses a friendlier entry point later.
- The tool has effectively no test suite, so changes to the CLI-and-Splitwise-SDK-entangled code are risky to make and hard to verify.

## Solution

Rebuild the expense-entry tool around a backend-agnostic core — Group, Participant, Expense, Split as domain objects, per [ADR 0001](../../docs/adr/0001-migrate-to-spliit.md) — sitting behind a single adapter interface, with Spliit (via its hosted instance at spliit.app) as the first and only implemented backend. On top of that core:

- Shared Expenses can be split across any chosen subset of a Group's Participants, not just two people.
- A Default Split Profile is saved per distinct set of Participants and auto-applied to future Shared Expenses involving that same set, pre-filled for one-keypress confirmation.
- A Category Suggestion is looked up by an Expense's description text (your own past description→Category choices first, then user-defined keyword rules) and pre-filled the same way.
- The CLI remains the first interface, built thin on top of the core so a future UI can be added without touching core logic.

Existing Splitwise groups and expense history are not migrated; they stay in Splitwise, read-only. Only new Expenses go through the rebuilt tool from now on.

## User Stories

1. As the tool's owner, I want the tool to talk to Spliit instead of Splitwise, so that I'm not forced to pay for API access I only use for a personal tool.
2. As the tool's owner, I want to configure "who am I" once per Group (since Spliit has no login/account concept), so that the tool knows which Participant's Paid Share to fill in as the Payer without asking me every run.
3. As the tool's owner, I want the tool to list the Groups that exist in my Spliit instance, so that I can choose which Group an Expense belongs to.
4. As the tool's owner, I want to record a Personal Expense under a Group containing only myself, so that I can track solo spending without it being split.
5. As the tool's owner, I want to record a Shared Expense against a chosen subset of a Group's Participants (not necessarily the whole Group), so that an Expense only involving some of a Group's members doesn't get incorrectly split across everyone.
6. As the tool's owner, I want to split a Shared Expense equally across 2 or more Participants, so that an expense shared with a whole household or trip group divides fairly without manual math.
7. As the tool's owner, I want to split a Shared Expense by exact amount across 2 or more Participants, so that I can match amounts to what each person actually consumed.
8. As the tool's owner, I want to split a Shared Expense by percentage across 2 or more Participants, so that I can apply an agreed cost-sharing ratio.
9. As the tool's owner, I want the tool to reject a Split whose shares don't sum to the Expense total (allowing for rounding), so that I don't upload an Expense with an inconsistent Split.
10. As the tool's owner, I want a Default Split Profile to be saved automatically the first time I choose a Split (method + shares) for a given set of Participants, so that I don't have to explicitly opt in to save it.
11. As the tool's owner, I want the tool to pre-fill and show a matching Default Split Profile for one-keypress confirmation whenever the same set of Participants recurs, so that recurring splits (e.g. always 70/30 with the same flatmate) don't need re-entry.
12. As the tool's owner, I want to override a pre-filled Default Split Profile for a one-off exception, so that an unusual Expense doesn't force me to permanently change the saved default.
13. As the tool's owner, I want overriding a Default Split Profile to update the saved default for that Participant set going forward, so that a changed arrangement (e.g. a new agreed percentage) only needs to be entered once.
14. As the tool's owner, I want each distinct set of Participants to have its own independent Default Split Profile, so that my split with Person A doesn't get confused with my split with Persons A and B together.
15. As the tool's owner, I want the tool to suggest a Category for an Expense based on its description text, so that I don't have to manually pick a Category for recurring merchants/descriptions.
16. As the tool's owner, I want the Category Suggestion to first check my own history of past description→Category choices, so that the suggestion reflects how I've actually categorized things before.
17. As the tool's owner, I want the Category Suggestion to fall back to user-defined keyword rules when a description has never been seen before, so that new-but-predictable descriptions (e.g. anything containing "Uber") still get a sensible suggestion.
18. As the tool's owner, I want the Category Suggestion pre-filled for one-keypress confirmation, so that confirming a good suggestion is as fast as confirming a Default Split Profile.
19. As the tool's owner, I want to override a suggested Category for a one-off case, so that a mis-suggested category doesn't force me to accept it.
20. As the tool's owner, I want an overridden Category choice to be recorded against that exact description text, so that future occurrences of the same description suggest the corrected Category.
21. As the tool's owner, I want to review each transaction from the cleaned CSV one at a time (date, amount, description, currency) before deciding whether to upload it, so that I can skip transactions that don't belong on the expense tracker (e.g. already-shared elsewhere, or a personal-only reimbursement).
22. As the tool's owner, I want to confirm all the collected details (Group, Participants, Split, Category) before the Expense is actually submitted, so that I catch mistakes before they're recorded.
23. As the tool's owner, I want a clear success or error message after each Expense submission attempt, so that I know whether it actually landed in Spliit.
24. As the tool's owner, I want a summary once all reviewed transactions have been processed, so that I know the run is complete.
25. As a future maintainer of this tool, I want the core split/profile/category/expense-construction logic to be backend-agnostic and interface-agnostic, so that swapping the backend again or adding a UI doesn't require rewriting business logic.
26. As a future maintainer of this tool, I want a single adapter interface between the core and Spliit, so that the core can be tested against a fake backend instead of a real or mocked Spliit connection.
27. As a future maintainer of this tool, I want the CLI to be a thin interface layer over the core, so that a future UI can be built by writing a new interface layer rather than duplicating business logic.
28. As the tool's owner, I want existing Splitwise Groups, Participants, and expense history left untouched in Splitwise, so that historical records remain available read-only without a data migration.

## Implementation Decisions

- **Backend-agnostic core**: introduce Group, Participant, Expense, Split, Payer, Default Split Profile, and Category Suggestion as domain objects/data structures independent of any backend SDK, matching the vocabulary in `CONTEXT.md`. All split math, Default Split Profile resolution, and Category Suggestion resolution operate purely on these domain objects — no network calls, no `input()`/`print()`.
- **Single backend adapter interface**: define one adapter interface (implemented first by a Spliit adapter, using Spliit's existing Python client library against the hosted spliit.app instance) exposing the operations the core needs: list Groups, list a Group's Participants, list Categories, and create an Expense (with its Splits). The core depends only on this interface, never on the Spliit client directly.
- **"Who am I" configuration**: since Spliit has no login/account concept, the Payer identity (which Participant is you) must be configured per Group rather than derived from an authenticated session. This is a one-time-per-Group configuration step, not re-asked per Expense.
- **N-person Split**: a Split is generalized from a fixed 2-party structure to an arbitrary chosen subset of a Group's Participants. Equal, Exact Amount, and Percentage split methods must all support 2 or more Participants. Exact Amount and Percentage splits must validate that entered shares sum to the Expense total (Exact Amount) or 100% (Percentage), within a small rounding tolerance, before the Split is accepted.
- **Default Split Profile storage and keying**: a Default Split Profile is keyed by the exact set of Participants involved in a Shared Expense (order-independent; a single other person is the size-1 case of this same mechanism). The first time a Split is chosen for a given Participant set, it is saved as that set's Default Split Profile. On a later Expense involving the same set, the saved profile is pre-filled and offered for one-keypress confirmation; explicitly overriding it updates the stored default for that set going forward.
- **Category Suggestion storage and keying**: a Category Suggestion is keyed by an Expense's description text, distinct from and orthogonal to Default Split Profiles. Resolution order: (1) exact match against the user's own prior description→Category choices, (2) fall back to user-defined keyword rules, (3) no suggestion if neither matches. An explicit override for a description is recorded so future occurrences of that same description suggest the corrected Category.
- **Persistence for profiles/suggestions**: Default Split Profiles and Category Suggestion history need durable local storage keyed as described above (participant-set key vs. description-text key). Concrete storage format (e.g. local file, embedded DB) is left to the implementer as a detail, provided the keying and resolution-order semantics above hold.
- **CLI as thin interface layer**: the CLI is rewritten to only gather input and render prompts/confirmations, delegating all decisions (split validity, profile/suggestion resolution, expense construction) to the core. It must not contain business logic that the core is responsible for.
- **Migration scope**: no automated migration of existing Splitwise Groups, Participants, or historical Expenses. Group/Participant setup in Spliit (including the "who am I" configuration) is done manually by the owner as a one-time setup step outside this tool.
- **Existing pipeline stages preserved**: the two-phase flow (clean a raw bank export into a normalized CSV, then walk through and upload each row as an Expense) is preserved as the overall shape; this spec covers reworking the upload phase's backend and split/category logic, not the CSV-cleaning phase.

## Testing Decisions

- Good tests here exercise the core pipeline (parse a normalized transaction → resolve Category Suggestion → resolve/apply Default Split Profile or collect an explicit Split → construct a backend-agnostic Expense → submit through the adapter) end-to-end against a **fake implementation of the single adapter interface**, asserting on what the fake received (which Groups/Participants were requested, what Expense+Split payload was submitted) — never asserting on internal call sequences or private helper methods.
- Split math (Equal/Exact Amount/Percentage across N Participants, including the sum-validation rules) should additionally be tested directly as pure functions, with no adapter or fake needed, covering 2-person, 3+-person, and rounding-edge cases (e.g. an equal split of an amount that doesn't divide evenly).
- Default Split Profile resolution (first-time save, pre-fill on Participant-set match, override-updates-default behavior, independence between different Participant sets) should be tested directly against its storage, independent of the CLI and the adapter.
- Category Suggestion resolution (history match, keyword-rule fallback, no-match case, override updates history) should likewise be tested directly against its storage.
- The CLI interface layer itself should not need its own business-logic tests, since it should contain none; if it grows any (e.g. input parsing/formatting), test those in isolation from the core.
- Prior art: `tests/test_upload_expenses.py` already fixtures user/friends/groups/group-members data for the current Splitwise-based class and is the closest existing analogue — its fixture style (plain dicts keyed by id) can inform the new Group/Participant fixtures, but its assertions are against the old two-person, Splitwise-SDK-coupled class and will need to be rewritten against the new adapter interface and domain objects rather than extended in place. `tests/test_clean_csv.py` is currently fully commented out and is not prior art to build on.

## Out of Scope

- A graphical/web UI. This spec only requires the core to be built interface-agnostically so a UI *can* be added later; building that UI is a separate piece of work.
- Migrating existing Splitwise Groups, Participants, or historical Expense data into Spliit.
- Multi-currency handling beyond whatever Spliit's API already supports natively — no new currency-conversion logic.
- Changes to the CSV-cleaning phase (`clean_csv.py` / `extract_wise_transactions.py`) beyond whatever is required to keep feeding the new upload phase the same normalized shape it produces today.
- Support for any backend other than Spliit (the adapter interface should make this possible later, but no second adapter is being built now).
- Automated data migration or backfill of Default Split Profiles / Category Suggestions from past manual usage — both start empty and build up from first use.

## Further Notes

- This spec deliberately bundles what PROJECT.md lists as four separate improvement items (Spliit migration, N-person split, default split profiles, category suggestions/UI groundwork) because ADR 0001 already ties them together: the backend swap and the N-person split rewrite were happening at the same time regardless, and the ADR's own rationale for building the adapter now (rather than a hard swap straight to Spliit's API) is that both changes want the same backend-agnostic core. Splitting them into fully independent specs would mean re-deciding the same seam twice.
- "What other optimizations can be implemented" (PROJECT.md item 5) is intentionally not addressed here — it's open-ended and better handled as its own follow-up once the rebuilt core exists to optimize.
- The exact Spliit Python client library and its call signatures were not verified against its current API surface as part of this spec; confirming its interface is implementation work, not a spec decision.

## Amendment (issue 08): User Story #3's "list the Groups that exist in my Spliit instance" assumed a capability Spliit doesn't have

User Story #3 and this spec's "Single backend adapter interface" decision both assumed the Spliit adapter's `list_groups()` could discover every Group that exists, the way Splitwise's SDK exposes a real `getGroups()` call. Confirmed false during issue 08: Spliit has no login/account concept, and the only Spliit operation available (`SpliitClient.get_group`, per [ADR 0002](../../docs/adr/0002-spliit-client-dependency-and-payer-identity.md)) requires a Group id the caller already has — there is no "all my Groups" endpoint to call. In practice, `list_groups()` has only ever been able to re-fetch a fixed set of ids supplied by the caller, which is why `run_shared_expense_cli.py` has required a required, repeatable `--group-id` argument since issue 05.

**Revised approach:** since every Group usable by `SharedExpenseCLI` already requires a Payer Configuration (issue 02's `WhoAmI`) to be usable at all, the Payer Configuration store doubles as the registry of "known" Groups: `run_shared_expense_cli.py` discovers Groups by reading every Group id that already has a Payer Configuration, rather than requiring them on the command line. A Group still has to be registered once, by pasting its id into `run_configure_who_am_i.py` — Spliit's lack of an enumeration API means the id has to come from somewhere outside the tool at least once — but that registration is never repeated on later runs. See [issue 08](issues/08-group-discovery-for-shared-expense-cli.md) for the full decision set and acceptance criteria.

This does not change the adapter interface itself (`list_groups()` still returns `List[Group]`, still takes ids from its caller) — only what supplies those ids to `SpliitExpenseBackend` at the `run_shared_expense_cli.py` wiring layer, plus resilience so one unfetchable Group doesn't abort an entire run.

## Amendment: Unify Personal and Shared Expense entry into a single flow

`run_expense_cli.py` (Personal Expenses) and `run_shared_expense_cli.py` (Shared Expenses) are two separate scripts today, each wired to its own CLI class (`PersonalExpenseCLI`, `SharedExpenseCLI` in `src/main/expense_cli.py`) and, notably, two different group-discovery mechanisms: the Personal script takes a single Group id via a required `--group-id` flag and never consults `WhoAmI`, inferring the Payer at runtime purely from the chosen Group having exactly one Participant; the Shared script takes no `--group-id` at all and instead discovers its Groups from every id already registered in `WhoAmI` (per issue 08's amendment above), filtered down to Groups with 2+ Participants. This split was never a deliberate design goal — it fell out of Personal Expense support (issue 03) landing before Shared Expense's group-discovery problem was solved (issue 08), leaving no reason to go back and unify them until now.

**Revised approach:** collapse both into one script and one CLI class covering every Expense type:

- **Single Group registry for both Expense types.** The unified flow drops `--group-id` entirely and sources *all* Groups — Personal and Shared alike — from `WhoAmI`'s registered ids, the same registry `SharedExpenseCLI` already uses. This means a Personal Expense Group must now also go through the one-time `run_configure_who_am_i.py` registration step before it can be used (previously not required, since the old Personal flow inferred the Payer at runtime without touching the registry). `run_configure_who_am_i.py` itself needs no code change — it already works correctly against a 1-Participant Group today (it lists Participants and asks "which one are you," with only one option to pick).
- **Group choice moves to per-transaction.** The unified flow prompts for which Group a transaction belongs to on every transaction, from the full registered list, the way `SharedExpenseCLI` already does — rather than the old Personal flow's behavior of pinning one Group for the entire CLI run via the `--group-id` flag. A run can now freely mix Personal and Shared Expenses transaction-by-transaction.
- **Participant count is the sole Personal/Shared signal, decided per-transaction.** Once a Group is chosen for a transaction, its Participant count alone decides the rest of the prompts: exactly 1 Participant skips participant-selection and Split-method prompts entirely and submits a Personal Expense (Payer = that Participant, `split=None`), exactly matching today's `PersonalExpenseCLI._resolve_payer_id` behavior; 2+ Participants runs the existing Shared Expense flow (choose Participants, choose Split) unchanged. No separate "is this Personal or Shared?" question is ever asked.
- **One script, one class.** `run_shared_expense_cli.py` is retired; `run_expense_cli.py` becomes the single entry point for all Expense types. `PersonalExpenseCLI` and `SharedExpenseCLI` are retired in favor of one CLI class covering both cases — their `run()` loops are near-identical (transaction iteration, review/skip, Category resolution, submit/confirm) and the merge is expected to remove that duplication rather than keep two classes behind one script.

This does not change the core domain objects, the adapter interface, split math, Default Split Profile, or Category Suggestion logic — only the CLI wiring layer (`src/main/expense_cli.py` and `src/scripts/`) and the one-time setup requirement that Personal Expense Groups now also need a Payer Configuration.
