# Automate Splitwise Expenses

This project arose from a personal need to optimize the amount of time I spent on creating expenses on a shared expense-tracking service (a big portion of it being toggling between my bank account and that service's tabs on my browser and selecting various parameters when creating an expense). So, to reduce the amount of time I've created this tool which is meant to be used as a command line utility.

Originally built against [Splitwise](https://secure.splitwise.com/), the tool now records expenses against [Spliit](https://spliit.app/)'s free hosted instance instead (Splitwise introduced API pricing - see [ADR 0001](docs/adr/0001-migrate-to-spliit.md)). Existing Splitwise groups and expense history are untouched and stay in Splitwise, read-only; only new expenses go through this tool from now on.

## Setup

The following pre-requisites are required before using the tool.
1. Clone this repo.
2. Install [Poetry](https://python-poetry.org/docs/#installation) on your local system.
3. Run the following commands:
    - `poetry shell`
    - `poetry install`
4. Spliit has no account/login - create the Group(s) you want to record expenses under directly at [spliit.app](https://spliit.app/), and note each Group's id (the path segment right after `groups/` in its URL, e.g. `https://spliit.app/groups/<GROUP_ID>/expenses`).

## Usage

Turning a bank export into Expenses recorded in Spliit is a three-phase process.

### Phase 1: Clean your CSV

1. You'll need a csv of the transactions you'd like to record (can be downloaded from your bank account).
2. Clean it into a normalized format ready for the next phases:
    - `poetry run python -m src.scripts.run_clean_csv <path to the csv file>`
3. Depending on the contents of the file, you will be asked a series of prompts that will be used to clean the csv file.
4. Once the file has been cleaned, it will be stored in the following directory `src/data/clean/` with the following name `<file name>_clean.csv`

### Phase 2: One-time per-Group setup ("who am I")

Spliit has no login, so before a Group can be used at all, the tool needs to know once which Participant is you:
- `poetry run python -m src.scripts.run_configure_who_am_i --group-id <GROUP_ID>`

This lists the Group's Participants, asks which one is you, and saves the answer locally (`who_am_i.json`, not committed) so it's never asked again for that Group. Every Group you want to submit Expenses against - Personal or Shared alike - must be registered this way at least once before it appears in Phase 3's Group picker.

### Phase 3: Submit expenses

- `poetry run python -m src.scripts.run_expense_cli src/data/clean/<file name>_clean.csv`

Review each transaction from the cleaned csv one at a time. For each one you confirm, you choose a registered Group; that Group's Participant count then decides the rest automatically:
- **Personal Expense** (a Group containing only yourself): submits immediately, no further prompts.
- **Shared Expense** (a Group with 2+ Participants): you choose the other Participants sharing the cost and a split method (Equal, Exact Amount, or Percentage). A previously-used split for the same set of Participants is offered again as a Default Split, so you're not asked to repeat it every time.

A single run can freely mix Personal and Shared Expenses, transaction by transaction.

## Legacy: Splitwise

The original Splitwise flow has been moved to [`obsolete/splitwise`](obsolete/splitwise) - see that folder's README. It's superseded by the Spliit flow above and not recommended for new use.

## To-Do
1. Automated verification that a submitted Expense actually reaches Spliit (currently a manual check).

## References
1. [Spliit](https://spliit.app/)
2. [Splitwise API](https://dev.splitwise.com/) (legacy)
3. [Splitwise Python SDK](https://github.com/namaggarwal/splitwise) (legacy)
