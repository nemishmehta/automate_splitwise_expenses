# 04: Update README setup/run instructions for uv

**What to build:** README's setup and usage sections tell a new contributor to install and run the project with uv, matching the actual, working commands post-migration — no stale Poetry instructions left behind.

**Blocked by:** 01 (Migrate pyproject.toml from Poetry to a non-packaged uv project)

**Status:** ready-for-agent

- [ ] Install step no longer references `poetry shell` / `poetry install`; replaced with the uv equivalent (e.g. `uv sync`)
- [ ] Every `poetry run python -m src.scripts.*` example (clean CSV, configure who-am-i, expense CLI) is rewritten as `uv run python -m src.scripts.*`
- [ ] No remaining references to Poetry in README.md
