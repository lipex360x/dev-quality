# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.1.1] — 2026-05-01

### Added
- `check-all` command: runs all checkers, ruff, mypy, vulture, bandit, pylint C0103, and shellcheck in a single `uvx` call
- `shellcheck-py` bundled as a dependency — no system install of shellcheck required
- `.dev-quality.yaml` local config file support: `skip`, `line_length`, `max_complexity`, `max_file_lines`, `max_func_lines`, `python_version`
- `check-all` registered as a pre-commit hook in `.pre-commit-hooks.yaml`
- ruff, mypy, vulture, bandit, pylint promoted to runtime dependencies (installed automatically via uvx)

### Fixed
- `check-bash-logs` and `check-bash-tests` now exit 0 silently when `scripts/bash/` does not exist — no false positives for Python-only repos

---

## [v0.1.0] — 2026-04-30

### Added
- Initial scaffold: `stacks/`, `shared/`, `tests/`, `pyproject.toml`, `.pre-commit-hooks.yaml`
- Python stack: 6 checkers migrated from `.brain`
  - `check-abbrev` — banned abbreviations in Python (AST) and Bash (regex)
  - `check-comments` — inline and block comments in Python and Bash
  - `check-complexity` — cyclomatic complexity of Bash functions (max 6)
  - `check-size` — file and function line limits (800 / 80)
  - `check-bash-tests` — paired test file coverage for Bash scripts
  - `check-bash-logs` — `log::init_script` presence in Bash scripts
- `shared/abbrev-rules.yaml` — cross-stack denylist and allowlist
- All checkers registered as pre-commit hooks
- 100% test coverage with pytest-cov (branch coverage enabled)

### Fixed
- `check-comments`: PEP 723 `# /// script` header blocks no longer flagged as comments
- `check-abbrev`: embedded defaults so the checker works when installed in a pre-commit venv (no YAML file required at runtime)
