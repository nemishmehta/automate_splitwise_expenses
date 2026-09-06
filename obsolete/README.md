# Obsolete

Code kept for reference only. Nothing here is exercised by CI (`testpaths` in `pyproject.toml`
scopes pytest to `tests/`) and none of it should be extended - it's archived, not maintained.

## `splitwise/`

The original Splitwise-backed flow, superseded by the Spliit flow described in the root
[README](../README.md) once Splitwise introduced API pricing (see
[ADR 0001](../docs/adr/0001-migrate-to-spliit.md)). Moved here as a unit since it doesn't share
any imports with the current `src/core` / `src/spliit` code:

- `upload_expenses.py` - the `UploadExpense` class (Splitwise SDK, one flat two-person split).
- `run_upload_expenses.py` - its CLI entrypoint.
- `test_upload_expenses.py` - its test suite.
- `.env_template` - template for the Splitwise `CONSUMER_KEY` / `CONSUMER_SECRET` / `API_KEY`
  this flow reads via `python-dotenv`.

To actually run this flow, copy `.env_template` to `.env` in this folder, fill in Splitwise
credentials, and run `poetry run python -m obsolete.splitwise.run_upload_expenses <csv path>`.
The `splitwise` and `python-dotenv` packages remain in `pyproject.toml` only for this.

## `test_clean_csv.py`

Test file for `src/main/clean_csv.py` (which is still active, current code - see Phase 1 in the
root README) that predates the `tests/main` reorg and was already fully commented out. Kept here
rather than deleted in case its fixture/assertion shape is useful groundwork for a real
replacement test.
