# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.6.1] — 2026-05-01

### Fixed
- `_collect()` no longer includes files that are staged in the git index but deleted from the working tree (`AD` status) — previously caused `PARSE_ERROR` and `READ_ERROR` for non-existent files

---

## [v0.6.0] — 2026-05-01

### Added
- `install-skill` command: copies the bundled `SKILL.md` to any AI assistant's skills directory (`install-skill --target ~/.claude/skills`); defaults to `~/.claude/skills` when `--target` is omitted
- `SKILL.md` bundled as package data in `dev_quality_skill` — full coding rules reference for Claude Code, installable via `/dev-quality` after running `install-skill`

---

## [v0.5.0] — 2026-05-01

### Added
- `semgrep` checker: runs automatically when the target project has a `.semgrep/` directory (with `.yml`/`.yaml` rules) or a `semgrep.yml`/`semgrep.yaml` at root; silently skipped when rules are absent or semgrep is not installed; respectable via `skip: [semgrep]` in `.dev-quality.yaml`
- `PLR2004` (magic value comparisons) now ignored in test files via `--per-file-ignores` for `tests/*.py`, `test_*.py`, and `*_test.py` patterns

---

## [v0.4.0] — 2026-05-01

### Added
- `--clear-cache` flag: removes `/tmp/dev-quality/` and exits
- `--no-cache` flag: disables ruff and mypy caching for the current run
- Cache hint printed after every run showing the cache location and both management commands
- `Scanning <root> ...` message printed at start so the terminal is never silent
- Per-checker findings now printed immediately as each checker completes (instead of batched at end)

### Changed
- Default cache behavior: ruff and mypy caches now go to `/tmp/dev-quality/{ruff,mypy}` (cross-platform via `tempfile.gettempdir()`) instead of being disabled — no pollution in the target project, cache persists within the session
- Checkers table in README reorganised by stack (Shared, Python, Bash)

---

## [v0.3.0] — 2026-05-01

### Added
- `--no-cache` flag for `check-all`: disables ruff and mypy caching for a single run

### Changed
- Default cache behavior: ruff (`--cache-dir`) and mypy (`--cache-dir`) now write to `/tmp/dev-quality/` instead of the target project

---

## [v0.2.1] — 2026-05-01

### Fixed
- `check-all` no longer creates `.ruff_cache/` or `.mypy_cache/` in the target project when run from inside it — `--no-cache` passed to ruff, `--no-incremental` to mypy

---

## [v0.2.0] — 2026-05-01

### Added
- `_collect()` now uses `git ls-files --cached --others --exclude-standard` so `.gitignore` is respected; falls back to `rglob` when not in a git repo
- `ruff check` now passes `--extend-ignore S101` to suppress false positives on `assert` in pytest files
- Formatted summary table at the end of every `check-all` run showing per-checker issue counts and total result

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
