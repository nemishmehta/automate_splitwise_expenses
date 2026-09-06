# 02: Spliit adapter + per-Group "who am I" configuration

**What to build:** A real implementation of the `ExpenseBackend` adapter interface against Spliit's hosted instance (spliit.app), using Spliit's existing Python client library. Since Spliit has no login/account concept, add a one-time per-Group configuration step that records which Participant is you, so the adapter knows whose Paid Share to fill in as the Payer.

**Blocked by:** 01 (core domain model + adapter interface)

**Status:** ready-for-agent

- [ ] The adapter implements list Groups, list a Group's Participants, list Categories, and create an Expense against the real Spliit hosted instance
- [ ] A configuration mechanism exists to record which Participant is "you" for each Group, set once and reused on subsequent runs without re-asking
- [ ] Creating an Expense through this adapter results in a real Expense visible in the corresponding Spliit Group
- [ ] Existing Splitwise Groups, Participants, and expense history are left untouched by this work
