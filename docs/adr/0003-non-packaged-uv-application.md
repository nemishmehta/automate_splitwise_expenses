---
status: accepted
---

# Treat the project as a non-packaged uv application, not an installable package

Poetry's `[tool.poetry]` declared `packages = [{include = "src"}]` and built via `poetry-core`, even though the tool has never been published to PyPI or installed from anywhere but its own repo root (`python -m src.scripts.*`). Migrating to uv, we set `[tool.uv] package = false` and dropped `build-system` entirely rather than swapping in a different backend (e.g. `hatchling`) to keep it installable — the packaging step was serving no purpose the actual usage pattern needed.

## Consequences

- `uv sync` no longer builds or installs `src` as a package; running any script requires the working directory to be the repo root (already true today, now load-bearing).
- If this tool is ever published or needs `pip install`-ing as a library from outside its own repo, this decision needs revisiting and a build backend re-added.
