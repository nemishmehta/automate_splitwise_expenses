# 04: Category Suggestion

**What to build:** Suggest a Category for an Expense keyed by its description text: check the owner's own history of past description→Category choices first, falling back to user-defined keyword rules for descriptions never seen before. Pre-fill the suggestion for one-keypress confirmation; recording an override against that exact description so future occurrences suggest the corrected Category.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** in-progress (core resolution logic done; CLI pre-fill deferred)

- [x] A suggested Category is looked up by an Expense's exact description text
- [x] The lookup checks the owner's own prior description→Category choices first
- [x] The lookup falls back to user-defined keyword rules when no prior exact match exists
- [x] No suggestion is shown when neither the history nor the keyword rules match
- [ ] The suggested Category is pre-filled and confirmable with a single keypress
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
- **Blocker for the remaining checkbox:** pre-filling the suggestion for
  one-keypress confirmation is a CLI concern and depends on issue 03's CLI
  existing, which in turn depends on issue 02 (real Spliit adapter) —
  treated as HITL since it needs the owner's actual, already-configured
  Spliit group to verify against. Once 03's CLI exists, wire
  `suggest_category` + `CategorySuggestionHistory` in there and check off
  the last box.
- User-defined keyword rules currently have no loader/config file — only
  `KeywordRule` the dataclass. Add a small loader (e.g. JSON file of
  `{keyword, category_id}` entries) when the CLI needs to supply rules;
  not needed yet since nothing constructs them outside tests.
