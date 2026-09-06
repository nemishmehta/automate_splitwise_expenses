# 04: Category Suggestion

**What to build:** Suggest a Category for an Expense keyed by its description text: check the owner's own history of past description→Category choices first, falling back to user-defined keyword rules for descriptions never seen before. Pre-fill the suggestion for one-keypress confirmation; recording an override against that exact description so future occurrences suggest the corrected Category.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** done

- [x] A suggested Category is looked up by an Expense's exact description text
- [x] The lookup checks the owner's own prior description→Category choices first
- [x] The lookup falls back to user-defined keyword rules when no prior exact match exists
- [x] No suggestion is shown when neither the history nor the keyword rules match
- [x] The suggested Category is pre-filled and confirmable with a single keypress
- [x] Overriding the suggestion for a description updates that description's stored Category choice for future runs

## Implementation notes (agent)

- `src/core/category_suggestion.py`: pure `suggest_category(description,
  history, keyword_rules)` resolver (history match, then first-matching
  `KeywordRule`, else `None`); `CategorySuggestionHistory` is a JSON-file-
  backed store (`get`/`record`) for the owner's own description→Category
  choices — `record` both saves a fresh choice and overrides an existing
  one, satisfying the override requirement. No I/O in the resolver itself,
  matching the no-I/O rule for core domain logic from issue 01.
- `history` is typed `Union[Dict[str, str], CategorySuggestionHistory]` and
  resolved via `.get()` so a plain dict (tests) and the real store
  (production) are interchangeable at that seam.
- Tests: `tests/core/test_category_suggestion.py` (10 tests) — resolution
  order/priority, keyword substring matching (case-insensitive, first match
  wins), and store persistence/override, built test-first per `/tdd`.
- **CLI pre-fill wiring (this iteration):** both `PersonalExpenseCLI` and
  `SharedExpenseCLI` (in `src/main/expense_cli.py`) now resolve a Category
  per transaction via a shared `_resolve_category` helper: it calls
  `suggest_category` (when a `CategorySuggestionHistory` is configured),
  prints the suggestion, and offers Enter-to-accept/any-key-to-decline —
  identical interaction shape to the Default Split Profile pre-fill from
  issue 07. Declining, or having no suggestion at all, falls through to a
  manual numbered choice from `backend.list_categories()`; a manual choice
  is recorded back into the history (covering both the "fresh choice" and
  "override" cases from the same code path, matching
  `CategorySuggestionHistory.record`'s dual purpose). When there are no
  Categories at all and no suggestion, the prompt is skipped entirely and
  `category_id` stays `None` — this is what kept every pre-existing test
  (none of which seed `FakeExpenseBackend` with Categories) passing
  unmodified, since production's `SpliitExpenseBackend.list_categories()`
  always returns a non-empty fixed taxonomy.
- Added `load_keyword_rules(path)` to `src/core/category_suggestion.py`: a
  small loader reading a JSON file of `{"keyword", "category_id"}` entries
  into `KeywordRule`s, returning `[]` when the file doesn't exist (this is
  user-authored config, not something the tool writes). Both
  `run_expense_cli.py` and `run_shared_expense_cli.py` now construct a
  `CategorySuggestionHistory` (`category_suggestion_history.json`) and
  `load_keyword_rules` (`category_keyword_rules.json`) at the repo root and
  pass them into their respective CLIs — both paths added to `.gitignore`
  as local per-operator files, mirroring `who_am_i.json` and
  `default_split_profiles.json`.
- Tests: 6 new tests in `tests/main/test_expense_cli.py` and 1 in
  `tests/main/test_shared_expense_cli.py` (suggestion accepted, suggestion
  declined + override recorded, no-suggestion manual choice + first-time
  record, choosing "None", keyword-rule fallback), plus 2 new tests for
  `load_keyword_rules` in `tests/core/test_category_suggestion.py`. All
  built test-first per `/tdd`; 124 tests pass total, flake8/isort/black
  clean on touched files.
- All checkboxes are now complete — this issue is done.
