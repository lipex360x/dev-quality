---
name: dev-quality
description: >-
  Guide for working inside the dev-quality repo. Use this skill when the user
  wants to add a new checker, fix a violation, understand a checker's output,
  run the suite locally, or release a new version.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# dev-quality — contributor guide

Central repo for code quality tooling. Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts for all stacks.

## Pre-flight

<pre_flight>

1. Confirm CWD is the dev-quality repo root — `ls pyproject.toml stacks/ tests/` must succeed.
2. Confirm the venv is ready — `uv run pytest --collect-only -q 2>&1 | tail -1` should list collected tests.
3. Confirm pre-commit hook is local — `grep "repo: local" .pre-commit-config.yaml` must match.

</pre_flight>

## Architecture

```
stacks/
  python/
    checkers/       ← standalone checker scripts (stdlib + pyyaml only)
  bash/
  typescript/       ← planned
shared/
  abbrev-rules.yaml ← banned abbreviations (cross-stack)
tests/              ← one test file per checker
skills/
  dev-quality/      ← this skill
.pre-commit-hooks.yaml
pyproject.toml
release.py
```

## Checkers

| Checker | Entry point | Scope |
|---------|-------------|-------|
| `check-abbrev` | `stacks/python/checkers/check_abbrev.py` | `.py` + `.sh` |
| `check-comments` | `stacks/python/checkers/check_comments.py` | `.py` + `.sh` |
| `check-size` | `stacks/python/checkers/check_size.py` | `.py` + `.sh` |
| `check-complexity` | `stacks/python/checkers/check_complexity.py` | `.sh` |
| `check-bash-tests` | `stacks/python/checkers/check_bash_tests.py` | dir |
| `check-bash-logs` | `stacks/python/checkers/check_bash_logs.py` | dir |
| `check-all` | `stacks/python/checkers/check_all.py` | orchestrator |

## Running checks

```bash
uv run check-all .           # full suite against this repo
uv run check-abbrev <file>   # individual checker
uv run pytest                # test suite (238 tests, 100% coverage required)
uv run pytest tests/check_size.test.py  # single file
```

## Configuration — `.dev-quality.yaml`

```yaml
# size
max_file_lines: 800   # default
max_func_lines: 100   # default (this repo uses 120)

# complexity
max_complexity: 6     # default

# style
line_length: 100      # default
python_version: "3.11"

# skip checkers
skip:
  - check-bash-logs
```

## Absolute rules

- **TDD** — test file first, implementation second. No exceptions.
- **No comments** — `.py` and `.sh` files allow only shebangs, `# noqa`, `# type: ignore`, `# pragma: no cover`.
- **No abbreviations** — reads `shared/abbrev-rules.yaml`.
- **Coverage: 100%** — checkers are small enough to cover fully.
- **Standalone checkers** — `check_abbrev`, `check_comments`, `check_size`, `check_complexity`, `check_bash_tests`, `check_bash_logs` use only stdlib + pyyaml.

## Adding a new checker

1. Write `tests/check_<name>.test.py` — run `uv run pytest tests/check_<name>.test.py` — must fail (red).
2. Write `stacks/python/checkers/check_<name>.py`.
3. Run tests until green.
4. Register in `.pre-commit-hooks.yaml` and in `_CUSTOM_FILE_CHECKERS` or `_CUSTOM_DIR_CHECKERS` in `check_all.py`.
5. Add the new checker entry point to `pyproject.toml` under `[project.scripts]`.
6. Document in `README.md`.

## Fixing common violations

| Code | Meaning | Fix |
|------|---------|-----|
| `FILE_TOO_LONG` | File exceeds `max_file_lines` | Split the file or raise limit in `.dev-quality.yaml` |
| `FUNC_TOO_LONG` | Function exceeds `max_func_lines` | Extract helpers or raise limit in `.dev-quality.yaml` |
| `ABBREV:<word>` | Banned abbreviation found | Expand: `cfg→config`, `buf→buffer`, `tmp→temporary`, etc. |
| `INLINE_COMMENT` | Inline comment found | Remove the comment — name the variable better instead |
| `BLOCK_COMMENT` | Block comment found | Remove; move intent to commit message or PR description |
| `COMPLEXITY:<n>` | Bash function too complex | Decompose into smaller functions |
| `MISSING_TEST` | `.sh` has no paired test | Create `tests/<name>.test.sh` |
| `MISSING_LOG_INIT` | `.sh` never calls `log::init_script` | Add the call at the top |

## Releasing

```bash
uv run release.py --dry-run   # preview tag + changelog
uv run release.py             # tag, push, create GitHub Release
```

**When to release** — only on behavior-changing commits (new checker, bug fix that affects output, new config param, new command). Never for docs, CLAUDE.md, or test-only commits.

**Version bump before release:**
1. `pyproject.toml` → `[project] version`
2. `CHANGELOG.md` → add entry
3. `README.md` → version badge

**Semver:**

| Change | Bump |
|--------|------|
| Bug fix | patch |
| New checker / config param / command | minor |
| Breaking: hook renamed, output format changed | major |

## Installing this skill

From the dev-quality repo root:

```bash
ln -sf "$(pwd)/skills/dev-quality" ~/.claude/skills/dev-quality
```

To uninstall:

```bash
rm ~/.claude/skills/dev-quality
```

## Self-audit

<self_audit>

1. **Pre-flight passed?** — repo root confirmed, venv ready, pre-commit is local
2. **TDD followed?** — test written before implementation for any new code
3. **Coverage at 100%?** — `uv run pytest --cov` shows no missed lines
4. **Pre-commit passes?** — `git commit` triggered hooks and all passed
5. **Release done?** — if behavior changed, version bumped and `release.py` run

</self_audit>
