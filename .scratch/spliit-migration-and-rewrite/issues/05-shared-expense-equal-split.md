# 05: Shared Expense — Equal split across N Participants

**What to build:** Let the owner choose a Group and a subset of 2 or more of its Participants (not necessarily the whole Group), and split an Expense equally among the chosen set as a Shared Expense. This establishes the Group/Participant-subset selection UI that later split-method tickets reuse.

**Blocked by:** 03 (end-to-end Personal Expense flow via the new CLI)

**Status:** in-progress (core split computation done; CLI selection deferred)

- [ ] Owner can choose a Group (other than a Personal Expense group) for a transaction
- [ ] Owner can choose a subset of 2+ Participants from that Group's members to share the Expense — the full Group is not required
- [x] An Equal split divides the Expense's total across the chosen Participants, with any rounding remainder assigned deterministically (e.g. to the Payer)
- [x] The Expense+Split submitted through the adapter correctly reflects the Payer's paid share and each Participant's owed share
- [x] Works for exactly 2 Participants and for 3 or more Participants

## Implementation notes (agent)

- `src/core/split.py`: pure `compute_equal_split(participant_ids, total,
  payer_id) -> Split`. Divides `total` by participant count, rounds each
  Share down to the cent (`ROUND_DOWN`), then adds the leftover remainder
  to the Payer's Share so Shares always sum exactly back to `total`.
  Raises `ValueError` if `payer_id` isn't among `participant_ids`
  (the <2-participants case is already covered by `Split.__post_init__`
  from issue 01, so no separate check was needed for that).
- Tests: `tests/core/test_split.py` (6 tests) — 2-participant even split,
  3-participant even split, 3-participant split with a rounding remainder
  (10 / 3, remainder assigned to Payer), both error cases, and one
  integration-style test building an `Expense` with the computed `Split`
  and submitting it through `FakeExpenseBackend`, asserting on what the
  fake received (per spec.md's Testing Decisions).
- **Blocker for the remaining two checkboxes:** "Owner can choose a
  Group"/"subset of Participants" are CLI-facing selection UI, which
  depends on issue 03's CLI — blocked on issue 02 (real Spliit adapter),
  both treated as HITL since they need the owner's real, already-
  configured Spliit group. Once 03's CLI exists, wire
  `compute_equal_split` in as the Equal-split option and check off the
  remaining boxes.
- This computation function is the reusable seam issues 06 (Exact/
  Percentage) and 07 (Default Split Profile) can build alongside, per the
  ticket's own note that 05 "establishes... later split-method tickets
  reuse."
