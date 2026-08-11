---
name: Migrated zip project runtime setup
description: What to check when a user imports/migrates a project as a zip and workflows fail with "command not found"
---

When a project is migrated from a zip (not a native Replit clone), the `.replit`
file, `package.json`, `pyproject.toml`, etc. may reference toolchains (node, pnpm,
uv, python) that are not actually installed as Nix modules yet, even though the
project's own config assumes they exist.

**Why:** Workflow failures like `bash: pnpm: command not found` or `node: command
not found` right after a zip import are almost always a missing-module problem,
not a code problem — don't start debugging application code first.

**How to apply:** Run `which node npm pnpm uv python3` early. If missing, use
`installProgrammingLanguage` for the needed node/python versions (check the
`.replit` `modules` line and `pyproject.toml` `requires-python` / lockfile for
the exact versions expected), then run the project's normal install step
(`pnpm install`, `uv sync --python <version>`) before touching workflows.
Multi-service migrated projects (e.g. a Python bot + a Node sidecar API) often
need one workflow per service; check the `.replit` workflow definitions for the
intended set of processes before assuming a single workflow suffices.
