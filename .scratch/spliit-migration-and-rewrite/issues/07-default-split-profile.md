# 07: Default Split Profile

**What to build:** Save a Split (method + shares) the first time it's used for a given set of Participants, keyed by that exact set (order-independent). Pre-fill and offer one-keypress confirmation when the same Participant set recurs on a later Expense. An explicit override updates the stored default for that set going forward, and each distinct Participant set keeps its own independent profile.

**Blocked by:** 05 (Shared Expense — Equal split across N Participants), 06 (Shared Expense — Exact Amount and Percentage splits across N Participants)

**Status:** ready-for-agent

- [ ] The first time a Split is chosen for a given set of Participants, it is saved as that set's Default Split Profile without requiring an explicit opt-in
- [ ] On a later Expense involving the exact same set of Participants (order-independent), the saved Default Split Profile is pre-filled and confirmable with a single keypress
- [ ] Overriding a pre-filled Default Split Profile updates the stored default for that Participant set going forward
- [ ] Two different Participant sets (e.g. {A} vs. {A, B}) maintain independent Default Split Profiles
- [ ] Works across all three split methods (Equal, Exact Amount, Percentage)
