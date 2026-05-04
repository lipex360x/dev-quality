# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.15.3] — 2026-05-04

### Added
- `check-all`: prints `Version: vX.Y.Z` before the `Cache:` line at the end of every run, making it clear which version of the validator is executing.

---

## [v0.15.2] — 2026-05-04

### Changed
- `check-repeated`: now skips assignments whose RHS is a **primitive literal** (`True`, `False`, `None`, integers, floats — including negatives). Eliminates false positives where the same flag is reset multiple times inside a state machine (e.g., `block_has_refs = False` × 3 within one function). String literal RHS (`API_PREFIX = "https://..."`) remains flagged — strings are still candidates for extraction as module-level constants.

---

## [v0.15.1] — 2026-05-04

### Changed
- `check-repeated`: scope narrowed to **value-derivation assignments only**. Now flags only lines matching `<identifier> = <expr>` where the RHS contains no function calls, subscripts, or container literals (no `(`, `[`, `{`), and the line does not end with `,`. This eliminates false positives from test boilerplate (`monkeypatch: pytest.MonkeyPatch,`), object construction (`mock = MagicMock(...)`), helper calls (`path = write_py(...)`), assertions (`assert ...`), and orchestrator patterns (`findings: list[str] = []`). Default `max_line_repetitions: 2` now usable on real codebases.
- `.dev-quality.yaml`: override reduced from `55` to `20`. Remaining repetitions are legitimate findings — repeated `tmp_path / "literal"` patterns across test functions that should be extracted to pytest fixtures. Tracked as TODO; not part of v0.15.1 scope.

### Documented
- Known limitation: `check-repeated` does not flag repeated function calls (`data = parse_config()` × 3) since string matching cannot infer purity. For cross-file duplicates, use `check-duplicate` (R0801).

---

## [v0.15.0] — 2026-05-04

### Added
- `check-repeated`: new checker for intra-file line repetition. Detects non-trivial lines repeated more than `max_line_repetitions` times within a single file (Python and Bash). Trivial lines (`pass`, `return None`, closing brackets, decorators, comments, docstring content, etc.) are filtered before counting. Config keys in `.dev-quality.yaml`: `max_line_repetitions` (default: `2`) and `min_line_length` (default: `20`). Disable with `skip: [check-repeated]`.
- `.dev-quality.yaml`: `max_line_repetitions: 55` set for this repo. `check_all.py` has 11+ identical boilerplate lines per checker function (architectural constraint — orchestrator can't extract across standalone checkers), and the 1000-line `check_all_main.test.py` has 50+ test functions each with the same fixture setup. Same pattern as `min_duplicate_lines: 20` for `check-duplicate`.

---

## [v0.14.0] — 2026-05-04

### Added
- `check-duplicate`: new checker using pylint R0801 to detect similar code blocks across production Python files. Test files are excluded. Runs only when ≥ 2 production files exist. Configurable via `min_duplicate_lines` in `.dev-quality.yaml` (default: `6`). Disable with `skip: [check-duplicate]`.

---

## [v0.13.2] — 2026-05-04

### Changed
- Default `line_length` changed from `100` to `120` across all layers: `check_all.py` default, `pyproject.toml`, `stacks/python/README.md`, `skill/SKILL.md`, and `README.md` config table.

---

## [v0.13.1] — 2026-05-04

### Changed
- `skill/` directory moved from `stacks/python/checkers/dev_quality_skill/` to the project root — the skill is language-agnostic and should not live inside the Python stack. Package name (`dev_quality_skill`) and all runtime behaviour are unchanged.

---

## [v0.13.0] — 2026-05-04

### Changed
- `SKILL.md` restructured into a language-agnostic Core layer. Python-specific rules moved to `python.md`; Bash-specific rules moved to `bash.md`. Adding a new language means adding a new `.md` file — the Core stays unchanged.
- `SKILL.md` frontmatter simplified to portable-only fields (`name`, `description`). Removed `allowed-tools` and `user-invocable` (Claude Code-only keys that caused VS Code agent warnings and limited portability to other AI tools).
- `install-skill` now copies all `.md` files from the package to `<target>/dev-quality/` instead of only `SKILL.md`. Future language files are installed automatically.
- `pyproject.toml`: package-data changed from `["SKILL.md"]` to `["*.md"]` so new language files are included in the wheel without manual intervention.

---

## [v0.12.1] — 2026-05-04

### Fixed
- `install-skill` was missing from `[project.scripts]` in `pyproject.toml` — the standalone `install-skill` command was not available when installed via `uvx`

---

## [v0.12.0] — 2026-05-04

### Added
- `install-skill`: saves the installation path to `~/.config/dev-quality/skill_path` after every install. Subsequent runs without `--target` read the saved path and update in-place — no need to remember the target directory.
- `check-all install-skill`: inherits the same behavior — `check-all install-skill` without `--target` uses the saved path.
- `install-skill`: new `_config_file()`, `_save_skill_path()`, `_load_skill_path()`, `_resolve_target()` helpers; `main()` accepts optional `config_file` kwarg for testability.

### Changed
- `check_all`: removed `_do_install_skill()` — `_handle_install_skill()` now delegates directly to `install_skill.main()` by setting `sys.argv`.

---

## [v0.11.0] — 2026-05-04

### Added
- `check-size`: test files now use a separate, higher line limit (default 1500) instead of the production file limit (default 800). Detects test files by directory (`tests/`, `test/`), name prefix (`test_*`), or suffix (`*_test.py`, `*.test.py`, `conftest.py`). Controlled via `CHECK_SIZE_MAX_TEST_FILE` env var.
- `check-all`: new `max_test_file_lines` config key in `.dev-quality.yaml` (default `1500`) passed to `check-size` via `CHECK_SIZE_MAX_TEST_FILE`.
- `check-all`: extracted `_build_size_env(config)` helper — consistent with `_build_abbrev_env` pattern.

---

## [v0.10.1] — 2026-05-04

### Fixed
- `check-noqa` was missing from `py-modules` in `pyproject.toml` — the module was not included in the built package
- `check-all`: outdated pre-commit warning now also appears after the summary, so it is not buried at the top of long output

---

## [v0.10.0] — 2026-05-04

### Added
- `check-noqa`: new checker that rejects inline `# noqa` and `# nosec` annotations — use `per-file-ignores` in `pyproject.toml` instead

### Changed
- Moved `S603`/`S607` suppressions from inline `# noqa` to `pyproject.toml` per-file-ignores
- Fixed `_warn_if_precommit_outdated` to catch specific exceptions instead of bare `except Exception`

---

## [v0.9.0] — 2026-05-04

### Added
- `check-all`: prints a `WARNING` when `.pre-commit-config.yaml` is pinned to an older `rev` than the installed version, with a `pre-commit autoupdate` hint

---

## [v0.8.1] — 2026-05-04

### Added
- `check-abbrev`: expanded denylist from 35 to 69 entries — covers common 3–5 char abbreviations that `min_length=2` alone does not catch: `addr`, `arg`, `arr`, `auth`, `avg`, `btn`, `cnt`, `conn`, `creds`, `desc`, `dir`, `hdr`, `hdrs`, `impl`, `info`, `lst`, `meta`, `param`, `params`, `perm`, `perms`, `prop`, `props`, `pwd`, `qry`, `qty`, `rec`, `resp`, `sess`, `tbl`, `tkn`, `tok`, `uri`, `url`

---

## [v0.8.0] — 2026-05-04

### Added
- `check-abbrev`: proactive short-name detection — identifiers with ≤ 2 characters are now flagged by default, not just denylist entries. `min_length` is configurable via `abbrev-rules.yaml` or `CHECK_ABBREV_MIN_LENGTH` env var.
- `check-all`: new `abbrev_min_length` and `abbrev_allowlist` config keys in `.dev-quality.yaml` passed to `check-abbrev` via environment variables.

### Changed
- `_DEFAULT_ALLOWLIST`: removed `io` — it is an abbreviation of Input/Output and should be spelled out.
- Loop variables are not exempt from abbreviation rules — use the full element name (`for finding in findings`, not `for f in findings`).

---

## [v0.7.2] — 2026-05-04

### Fixed
- `release.py`: `_update_readme_version` now also rewrites all `rev: v<old>` references in README examples — they were previously left behind after every version bump

---

## [v0.7.1] — 2026-05-04

### Fixed
- `check_all`: mypy no longer scans test files (`tests/`, `test_*.py`, `*_test.py`, `conftest.py`) — avoids false `[untyped-decorator]` failures in isolated environments where pytest is not installed

---

## [v0.7.0] — 2026-05-01

### Changed
- `release.py` now reads the version from CHANGELOG (source of truth) instead of `pyproject.toml`
- `release.py` now updates `pyproject.toml` and the README badge automatically — no manual edits needed
- New `--release` flag: tag + GitHub Release only created when this flag is passed; default run commits version bump only
- `_commit_readme_version` replaced by `_commit_version_bump` which stages both `pyproject.toml` and `README.md`

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
