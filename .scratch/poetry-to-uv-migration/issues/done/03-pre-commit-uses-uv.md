# 03: Update pre-commit hooks to use uv

**What to build:** Local pre-commit hooks invoke isort, black, flake8, and pytest through uv instead of Poetry, so `git commit` works for contributors on the uv-based setup.

**Blocked by:** 01 (Migrate pyproject.toml from Poetry to a non-packaged uv project)

**Status:** ready-for-agent

- [ ] `.pre-commit-config.yaml`'s `isort`, `black`, `flake8`, and `pytest` hook entries run `uv run <tool>` instead of `poetry run <tool>`
- [ ] Running `pre-commit run --all-files` (or making a commit) executes all four hooks successfully with no Poetry installed
