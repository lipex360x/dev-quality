# dev-quality

> Quality tooling for Python and Bash — enforced via pre-commit or on-demand via uvx.

Central repository for code quality tooling across stacks. Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts. Single source of truth — no more copying tools across projects.

[![Version](https://img.shields.io/badge/version-v0.5.0-blue)](https://github.com/lipex360x/dev-quality/releases)

---

## Contents

- [Checkers](#checkers)
- [Prerequisites](#prerequisites)
- [How to use](#how-to-use)
  - [One-off analysis — uvx](#one-off-analysis--uvx-no-install-required)
  - [Permanent install — uv](#permanent-install--uv)
  - [Automated on every commit — pre-commit](#automated-on-every-commit--pre-commit)
- [Running specific checkers](#running-specific-checkers)
- [check-all behavior](#check-all-behavior)
- [Local configuration](#local-configuration----dev-qualityyaml)
- [Individual hooks](#individual-hooks)
- [Local development](#local-development)
- [Stacks](#stacks)

---

## Checkers

### Shared — Python and Bash

| Hook | What it validates |
|---|---|
| `check-abbrev` | Banned abbreviations (`buf`, `cfg`, `ref`, `tmp`, etc.) |
| `check-comments` | Inline and block comments (except shebangs, `# shellcheck`, `# noqa`, `# type: ignore`, PEP 723 blocks) |
| `check-size` | Files over 800 lines or functions over 80 lines |

### Python

| Hook | What it validates |
|---|---|
| `ruff check` | Linting: imports, style, bugs, McCabe complexity, security; PLR2004 suppressed in test files |
| `ruff format` | Code formatting |
| `mypy` | Static type checking in strict mode |
| `vulture` | Dead code (unused functions, variables, imports) |
| `bandit` | Security vulnerabilities |
| `pylint C0103` | Variable and function naming conventions |
| `semgrep` | Custom rules — runs automatically when `.semgrep/` or `semgrep.yml` exists at project root |

### Bash

| Hook | What it validates |
|---|---|
| `check-complexity` | Functions with cyclomatic complexity above 6 |
| `check-bash-tests` | Every `.sh` outside `hooks/` and `tests/` must have a paired test file |
| `check-bash-logs` | Every `.sh` outside `hooks/`, `tests/` and `lib/` must call `log::init_script` |
| `shellcheck` | Bugs and bad practices in shell scripts |

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — used to run checkers without a manual install
- **Git** — required for the `git+https://` install form

> [!NOTE]
> No system install of shellcheck is needed — `shellcheck-py` bundles the binary and is installed automatically.

---

## How to use

### One-off analysis — `uvx` (no install required)

Run all checkers against any project without installing anything permanently:

```bash
# from inside the target project
cd /path/to/project
uvx --from git+https://github.com/lipex360x/dev-quality check-all .

# or from anywhere, passing the path
uvx --from git+https://github.com/lipex360x/dev-quality check-all /path/to/project

# disable caching entirely
uvx --from git+https://github.com/lipex360x/dev-quality check-all --no-cache .
```

`uvx` fetches the package into a temporary environment, runs the command, and discards it. Useful for auditing a project before setting up pre-commit, or in CI without prior setup.

> [!NOTE]
> No cache directories (`.mypy_cache/`, `.ruff_cache/`) are ever created in the target
> project. By default, caches go to the system temp directory (`/tmp/dev-quality/`).
> Pass `--no-cache` to disable caching entirely.

### Permanent install — `uv`

Install once and run the commands directly from any terminal session:

```bash
uv tool install git+https://github.com/lipex360x/dev-quality
```

Then use any checker without the `uvx --from ...` prefix:

```bash
# from inside the target project
check-all .

# or passing the path
check-all /path/to/project
check-abbrev src/main.py
```

### Automated on every commit — pre-commit

Add to the target project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.5.0
    hooks:
      - id: check-all
```

Then install the hooks:

```bash
pre-commit install
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Running specific checkers

File-based checkers accept one or more file paths:

```bash
# Check for banned abbreviations
uvx --from git+https://github.com/lipex360x/dev-quality check-abbrev src/main.py scripts/deploy.sh

# Check for disallowed comments
uvx --from git+https://github.com/lipex360x/dev-quality check-comments src/main.py

# Check file and function size
uvx --from git+https://github.com/lipex360x/dev-quality check-size src/main.py scripts/deploy.sh

# Check Bash function complexity
uvx --from git+https://github.com/lipex360x/dev-quality check-complexity scripts/deploy.sh
```

Directory-based checkers accept a project root (defaults to `git rev-parse --show-toplevel`):

```bash
# Check every Bash script has a paired test
uvx --from git+https://github.com/lipex360x/dev-quality check-bash-tests /path/to/project

# Check every Bash script calls log::init_script
uvx --from git+https://github.com/lipex360x/dev-quality check-bash-logs /path/to/project
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## check-all behavior

- **`.gitignore` respected** — file collection uses `git ls-files` when the target is a git repository, so ignored files and directories are never checked. Falls back to recursive scan when outside a git repo.
- **Progress as it runs** — each checker prints findings immediately; a `Scanning ...` message appears at start so the terminal is never silent.
- **No side effects** — caches go to the system temp directory, never to the target project.
- **Summary at the end** — per-checker status table followed by cache location and management options:

```
──────────────────────────────────────
 check-abbrev       FAIL   12 issues
 check-comments     PASS
 ruff check         FAIL   15 issues
 mypy               PASS
 ...
──────────────────────────────────────
 Result             FAIL   27 issues
──────────────────────────────────────
Cache: /tmp/dev-quality
  To clear:   check-all --clear-cache
  To disable: check-all --no-cache .
```

**Cache commands:**

```bash
# clear the cache
check-all --clear-cache

# run without using or writing cache
check-all --no-cache .
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Local configuration — `.dev-quality.yaml`

Create a `.dev-quality.yaml` at the project root to customize `check-all` behavior:

```yaml
# Checkers to skip (any combination of the names below)
# check-abbrev, check-comments, check-size, check-complexity,
# check-bash-tests, check-bash-logs,
# ruff, mypy, vulture, bandit, pylint, shellcheck, semgrep
skip:
  - check-bash-logs
  - check-bash-tests

# Maximum line length (default: 100)
line_length: 120

# Maximum cyclomatic complexity for Bash and Python functions (default: 6)
max_complexity: 8

# Maximum number of lines per file (default: 800)
max_file_lines: 1000

# Maximum number of lines per function (default: 80)
max_func_lines: 100

# Python version for mypy (default: "3.11")
python_version: "3.12"
```

The file is optional — defaults above apply when it is absent.

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Individual hooks

To use specific checkers instead of `check-all`:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.5.0
    hooks:
      - id: check-abbrev
      - id: check-comments
      - id: check-size
      - id: check-complexity
      - id: check-bash-tests
      - id: check-bash-logs
```

> [!IMPORTANT]
> Individual hooks do not include ruff, mypy, vulture, bandit, pylint, and shellcheck.
> Use `check-all` to run the full suite.

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Local development

```bash
git clone https://github.com/lipex360x/dev-quality
cd dev-quality
uv sync
uv run pytest
```

All checkers live in `stacks/python/checkers/`. Tests live in `tests/`. Coverage must stay at 100%.


<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Stacks

| Stack | Status |
|---|---|
| Python | in progress |
| Bash | in progress |
| TypeScript | planned |

---

Tooling decisions are documented in the [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint).
This repo is the implementation — the blueprint is the spec.
