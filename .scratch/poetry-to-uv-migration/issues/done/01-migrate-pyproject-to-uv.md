# 01: Migrate pyproject.toml from Poetry to a non-packaged uv project

**What to build:** Replace the project's Poetry configuration with a uv-managed, non-packaged setup, per [ADR 0003](../../../docs/adr/0003-non-packaged-uv-application.md). After this ticket, `uv sync` installs dependencies without building/installing `src` as a package, and `uv run python -m src.scripts.*` works from the repo root.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `[tool.poetry]` table replaced with a standard `[project]` table (name, version, description, authors, license, dependencies) plus dev dependencies expressed the uv way (e.g. `[dependency-groups]` or `[tool.uv]`)
- [ ] `[tool.uv] package = false` set
- [ ] `[build-system]` section removed entirely (no build backend)
- [ ] `poetry.lock` removed and `uv.lock` generated and committed
- [ ] `uv sync` succeeds and does not attempt to build/install `src` as a package
- [ ] `uv run python -m src.scripts.run_expense_cli --help` (or equivalent) runs successfully from the repo root
