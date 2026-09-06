# 06: Shared Expense — Exact Amount and Percentage splits across N Participants

**What to build:** Let the owner split a Shared Expense by exact amount or by percentage across the chosen 2+ Participants, validating that entered shares sum to the Expense total (Exact Amount) or 100% (Percentage), within a small rounding tolerance, before the Split is accepted.

**Blocked by:** 05 (Shared Expense — Equal split across N Participants)

**Status:** ready-for-agent

- [ ] Owner can choose Exact Amount as the split method and enter an amount for each non-Payer Participant
- [ ] An Exact Amount split is rejected, with a re-prompt, if entered shares don't sum to the Expense total (within a small rounding tolerance)
- [ ] Owner can choose Percentage as the split method and enter a percentage for each non-Payer Participant
- [ ] A Percentage split is rejected, with a re-prompt, if entered percentages don't sum to 100% (within a small rounding tolerance)
- [ ] Both methods work for exactly 2 Participants and for 3 or more Participants
