# 07: Default Split Profile

**What to build:** Save a Split (method + shares) the first time it's used for a given set of Participants, keyed by that exact set (order-independent). Pre-fill and offer one-keypress confirmation when the same Participant set recurs on a later Expense. An explicit override updates the stored default for that set going forward, and each distinct Participant set keeps its own independent profile.

**Blocked by:** 05 (Shared Expense — Equal split across N Participants), 06 (Shared Expense — Exact Amount and Percentage splits across N Participants)

**Status:** complete

- [x] The first time a Split is chosen for a given set of Participants, it is saved as that set's Default Split Profile without requiring an explicit opt-in
- [x] On a later Expense involving the exact same set of Participants (order-independent), the saved Default Split Profile is pre-filled and confirmable with a single keypress
- [x] Overriding a pre-filled Default Split Profile updates the stored default for that Participant set going forward
- [x] Two different Participant sets (e.g. {A} vs. {A, B}) maintain independent Default Split Profiles
- [x] Works across all three split methods (Equal, Exact Amount, Percentage)

## Implementation notes (agent)

- `src/core/default_split_profile.py`: `SplitProfile` (frozen dataclass:
  `method: SplitMethod`, `values: Optional[Dict[str, Decimal]]` — raw
  per-Participant percentages/exact-amounts as entered, or `None` for
  Equal, which needs nothing but the method to be recomputed against a new
  total) and `DefaultSplitProfileStore`, a JSON-file-backed store
  (`get`/`record`) keyed by the Participant id set normalized via
  `sorted(set(participant_ids))` joined into a stable string — the same
  precedent as `CategorySuggestionHistory`/`WhoAmI`. Decimals persist as
  strings, round-tripped through `Decimal(str(...))`.
- `src/main/expense_cli.py`'s `SharedExpenseCLI` takes an optional
  `default_split_profiles: Optional[DefaultSplitProfileStore] = None`
  constructor argument (backward compatible - `None` disables the feature
  entirely, matching every pre-existing test). `_choose_split` first checks
  for a stored profile for the chosen Participant set; if found, prints a
  summary and asks for a single-keypress confirm/decline exactly like the
  existing submit/cancel prompts elsewhere in this file. Confirming
  recomputes the stored method+values against the *current* total/payer
  (so Percentage profiles generalize across differing totals; Exact
  profiles only succeed if the new total still matches the stored exact
  amounts' sum - declining or an amount mismatch both fall through to the
  normal method-choice flow). Every freshly computed split (first use,
  decline-then-rechoose, or no profile at all) is recorded back into the
  store as that set's new default. `_prompt_split` now returns both the
  raw entered values and the computed `Split` so the raw values (not the
  computed absolute amounts) are what gets persisted.
- `src/scripts/run_shared_expense_cli.py`: constructs a
  `DefaultSplitProfileStore` against `default_split_profiles.json` at the
  repo root (mirrors `who_am_i.json`'s wiring), added to `.gitignore` as
  local per-operator state.
- **Pre-existing config bug found & fixed while adding this file**:
  `pyproject.toml`'s `[tool.isort]` had no `line_length`, so isort's
  `profile = "black"` default (88) disagreed with this repo's actual
  `[tool.black]` `line-length = 79`, letting isort collapse an import onto
  an 81-char line that black would then want to re-wrap (an isort/black
  fight). Added `line_length = 79` under `[tool.isort]` so both tools
  agree; confirmed via `git stash` that no other tracked file was
  previously affected by this latent mismatch.
- Tests: `tests/core/test_default_split_profile.py` (7 tests: get/record,
  order-independence, independent sets, persistence, override) and new
  cases added to `tests/main/test_shared_expense_cli.py` (first-use save,
  pre-fill + single-Enter confirm across a different comma order, decline
  falls through and overrides the stored default, two participant sets
  stay independent) - all via the existing scripted-`input_fn` pattern, no
  real I/O in the CLI tests (`DefaultSplitProfileStore` still uses a real
  `tmp_path` JSON file, matching how `CategorySuggestionHistory` is tested
  elsewhere).
- Full suite: 113 passed. `black`, `isort`, `flake8` all clean on every
  file touched by this issue (one pre-existing, unrelated `black`
  violation in `src/main/extract_wise_transactions.py` predates this work
  and was left untouched).
