# 04: Category Suggestion

**What to build:** Suggest a Category for an Expense keyed by its description text: check the owner's own history of past description→Category choices first, falling back to user-defined keyword rules for descriptions never seen before. Pre-fill the suggestion for one-keypress confirmation; recording an override against that exact description so future occurrences suggest the corrected Category.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** ready-for-agent

- [ ] A suggested Category is looked up by an Expense's exact description text
- [ ] The lookup checks the owner's own prior description→Category choices first
- [ ] The lookup falls back to user-defined keyword rules when no prior exact match exists
- [ ] No suggestion is shown when neither the history nor the keyword rules match
- [ ] The suggested Category is pre-filled and confirmable with a single keypress
- [ ] Overriding the suggestion for a description updates that description's stored Category choice for future runs
