# 03: End-to-end Personal Expense flow via the new CLI

**What to build:** Rewrite the CLI as a thin interface layer over the core. It reads the cleaned CSV, presents each transaction for review, lets the owner submit a transaction as a Personal Expense (a Group containing only themself), shows a success/error message per submission, and prints a summary once all transactions have been processed. This is the first fully demoable end-to-end slice, run against real Spliit.

**Blocked by:** 01 (core domain model + adapter interface), 02 (Spliit adapter + who am I configuration)

**Status:** ready-for-agent

- [ ] CLI reads a cleaned CSV (date, amount, description, currency) and presents each transaction for review, one at a time
- [ ] Owner can skip a transaction without uploading it
- [ ] Owner can choose to submit a transaction as a Personal Expense against a Group containing only themself
- [ ] Collected details are shown for confirmation before the Expense is actually submitted
- [ ] A clear success or error message appears after each submission attempt
- [ ] A summary is shown once all reviewed transactions have been processed
- [ ] The CLI contains no business logic (e.g. split validity, Expense construction) — it only gathers input and calls the core
