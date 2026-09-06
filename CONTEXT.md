# Automate Splitwise Expenses

A personal tool that turns a bank transaction export into expenses recorded in a shared expense-tracking backend, split across the people who owe part of the cost.

## Language

**Participant**:
Anyone selectable to share the cost of an Expense, including yourself.
_Avoid_: Friend, user (the old Splitwise-specific term — meaningless once the backend has no login/friends concept)

**Group**:
A named, persistent collection of Participants that Expenses are recorded under.

**Personal Expense**:
An Expense recorded under a Group containing only yourself — tracked for your own records but never split with anyone.
_Avoid_: Unsplit expense

**Shared Expense**:
An Expense split, via a Split, across a chosen subset of a Group's Participants (not necessarily the whole Group).

**Split**:
The method used to divide a Shared Expense's cost among its Participants: Equal, Exact Amount, or Percentage. You are always the Payer; the Split determines what each other Participant owes you.
_Avoid_: Share (ambiguous between the method and one participant's resulting amount)

**Payer**:
The Participant who fronted the money for an Expense. Always you, since Expenses originate from your own bank transactions.

**Default Split Profile**:
A saved Split (method + shares) keyed by a specific *set* of Participants (a single other person is just the size-1 case), applied automatically to future Shared Expenses involving that same set unless overridden.

**Category Suggestion**:
A suggested Category for an Expense, keyed by its description text rather than its Participants. Checked against your own history of past description-to-Category choices first, falling back to user-defined keyword rules for descriptions never seen before. Pre-filled and shown for one-keypress confirmation, same UX as a Default Split Profile, but a distinct concept: it keys off *what* was bought, not *who* it was split with.
