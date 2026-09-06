# 02: Update CI workflow to use uv

**What to build:** The GitHub Actions test workflow installs and invokes tooling through uv instead of Poetry, so CI reflects the same setup contributors use locally.

**Blocked by:** 01 (Migrate pyproject.toml from Poetry to a non-packaged uv project)

**Status:** ready-for-agent

- [ ] `.github/workflows/tests.yaml` no longer installs or configures Poetry (drops `POETRY_VERSION`, `pip install poetry`, `poetry config`, `poetry install`)
- [ ] Workflow sets up uv (e.g. via `astral-sh/setup-uv`) and runs `uv sync`
- [ ] isort, black, flake8, and pytest steps run via `uv run` instead of `poetry run`
- [ ] Workflow passes on a branch/PR after the change
