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

Spliit has no login, so before submitting any **Shared Expense** (an Expense split across 2+ Participants of a Group), the tool needs to know once which Participant is you:
- `poetry run python -m src.scripts.run_configure_who_am_i --group-id <GROUP_ID>`

This lists the Group's Participants, asks which one is you, and saves the answer locally (`who_am_i.json`, not committed) so it's never asked again for that Group. Skip this step for a **Personal Expense Group** (a Group containing only yourself) - the tool infers the payer automatically since there's only one Participant to choose from.

### Phase 3: Submit expenses

Review each transaction from the cleaned csv one at a time and submit the ones you confirm, either as a Personal Expense or a Shared Expense.

- **Personal Expense** (a Group containing only yourself):
    - `poetry run python -m src.scripts.run_expense_cli --group-id <GROUP_ID> src/data/clean/<file name>_clean.csv`
- **Shared Expense** (split across a chosen subset of a Group's Participants; repeat `--group-id` to offer a choice of multiple Groups):
    - `poetry run python -m src.scripts.run_shared_expense_cli --group-id <GROUP_ID> [--group-id <GROUP_ID_2> ...] src/data/clean/<file name>_clean.csv`
    - For each confirmed transaction, you'll choose a Group, the other Participants sharing the cost, and a split method (Equal, Exact Amount, or Percentage). A previously-used split for the same set of Participants is offered again as a Default Split, so you're not asked to repeat it every time.

## Legacy: Splitwise

The original Splitwise flow has been moved to [`obsolete/splitwise`](obsolete/splitwise) - see that folder's README. It's superseded by the Spliit flow above and not recommended for new use.

## To-Do
1. Automated verification that a submitted Expense actually reaches Spliit (currently a manual check).

## References
1. [Spliit](https://spliit.app/)
2. [Splitwise API](https://dev.splitwise.com/) (legacy)
3. [Splitwise Python SDK](https://github.com/namaggarwal/splitwise) (legacy)
