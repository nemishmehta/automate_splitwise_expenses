# 05: Shared Expense — Equal split across N Participants

**What to build:** Let the owner choose a Group and a subset of 2 or more of its Participants (not necessarily the whole Group), and split an Expense equally among the chosen set as a Shared Expense. This establishes the Group/Participant-subset selection UI that later split-method tickets reuse.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** ready-for-agent

- [ ] Owner can choose a Group (other than a Personal Expense group) for a transaction
- [ ] Owner can choose a subset of 2+ Participants from that Group's members to share the Expense — the full Group is not required
- [ ] An Equal split divides the Expense's total across the chosen Participants, with any rounding remainder assigned deterministically (e.g. to the Payer)
- [ ] The Expense+Split submitted through the adapter correctly reflects the Payer's paid share and each Participant's owed share
- [ ] Works for exactly 2 Participants and for 3 or more Participants
