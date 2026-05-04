# dev-quality

> Quality tooling for Python and Bash — enforced via pre-commit or on-demand via uvx.

Central repository for code quality tooling across stacks. Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts. Single source of truth — no more copying tools across projects.

[![Version](https://img.shields.io/badge/version-v0.15.0-blue)](https://github.com/lipex360x/dev-quality/releases)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org)

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
- [AI assistant skill](#ai-assistant-skill)
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
| `check-repeated` | Same value-derivation assignment (`name = pure_expr`) repeated more than `max_line_repetitions` times in a file (e.g., `gitignore = project / ".gitignore"` × 3). Skips function calls, subscripts, container literals, and annotated assignments to keep noise low |
| `check-size` | Files over 800 lines or functions over 80 lines |

### Python

| Hook | What it validates |
|---|---|
| `check-noqa` | Inline `# noqa` and `# nosec` annotations — use `per-file-ignores` in `pyproject.toml` instead |
| `ruff check` | Linting: imports, style, bugs, McCabe complexity, security; PLR2004 suppressed in test files |
| `ruff format` | Code formatting |
| `mypy` | Static type checking in strict mode |
| `vulture` | Dead code (unused functions, variables, imports) |
| `bandit` | Security vulnerabilities |
| `pylint C0103` | Variable and function naming conventions |
| `check-duplicate` | Duplicate code blocks (pylint R0801) — production files only, ≥ 2 files required |
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

**Updating to the latest version:**

```bash
uv tool install git+https://github.com/lipex360x/dev-quality --reinstall
```

To pin to a specific release:

```bash
uv tool install git+https://github.com/lipex360x/dev-quality@v0.8.1 --reinstall
```

### Automated on every commit — pre-commit

[pre-commit](https://pre-commit.com) is a tool that runs checks automatically every time you run `git commit`. If any checker fails, the commit is blocked until the issue is fixed — no bad code reaches the repository.

**1. Install pre-commit** (once per machine):

```bash
# Cross-platform
pip install pre-commit

# macOS
brew install pre-commit

# Windows
winget install pre-commit
# or: scoop install pre-commit
# or: choco install pre-commit
```

**2. Create `.pre-commit-config.yaml`** at the root of the target project:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.15.0
    hooks:
      - id: check-all
```

**3. Activate the hooks** in that project (once per clone):

```bash
pre-commit install
```

From this point on, every `git commit` runs all checkers automatically. If a check fails, the commit is aborted and the findings are printed so you can fix them before trying again.

> [!TIP]
> To run all checkers manually without committing:
> ```bash
> pre-commit run --all-files
> ```

> [!TIP]
> To update dev-quality to the latest released version:
> ```bash
> pre-commit autoupdate --repo https://github.com/lipex360x/dev-quality
> ```
> This updates the `rev` in `.pre-commit-config.yaml` to the newest tag.

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

## check-abbrev — abbreviation rules

Two complementary rules run together:

**1. Short names (length ≤ 2, default)**
Any identifier with 2 or fewer characters is flagged — unless it appears in the allowlist.

**2. Known abbreviations (any length)**
Names in the denylist are always flagged regardless of length. The full list is in [`shared/abbrev-rules.yaml`](shared/abbrev-rules.yaml). Key entries:

| Category | Flagged names |
|---|---|
| Config / context | `cfg`, `ctx`, `opts` |
| Error handling | `err`, `exc` |
| Data / types | `attr`, `buf`, `obj`, `val`, `var` |
| I/O | `img`, `src`, `dst`, `dest` |
| Structure | `arr`, `lst`, `rec`, `tbl` |
| Network / auth | `url`, `uri`, `auth`, `conn`, `sess`, `creds` |
| Naming | `arg`, `param`, `params`, `prop`, `props` |
| Misc | `avg`, `cnt`, `desc`, `dir`, `hdr`, `impl`, `info`, `meta`, `perm`, `perms`, `pwd`, `qry`, `qty`, `resp`, `tmp`, `tkn` |

**Default allowlist — names that are never flagged:**

| Name | Reason |
|---|---|
| `i`, `j`, `k` | Loop counters — universal convention |
| `_` | Throwaway variable — universal convention |
| `id` | Identifier — used across all languages |
| `ok` | Boolean result — idiomatic in Python/Go |
| `self`, `cls` | Python instance/class receivers |
| `args`, `kwargs` | Python variadic parameters |

**Extending the allowlist for your project**

Add an `abbrev_allowlist` key to `.dev-quality.yaml` at the project root. These names are merged with the defaults — no defaults are removed:

```yaml
# .dev-quality.yaml
abbrev_allowlist:
  - py    # short for "Python files" in file-list variables
  - sh    # short for "Shell files" in file-list variables
```

To raise the minimum length (flag names ≤ 3 chars instead of ≤ 2):

```yaml
# .dev-quality.yaml
abbrev_min_length: 3
```

To disable length-based checking entirely (denylist only):

```yaml
# .dev-quality.yaml
abbrev_min_length: 0
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## check-repeated — scope and limitations

`check-repeated` deliberately targets a narrow class of duplication: **the same value-derivation assignment computed N+ times in the same file**. It is meant to catch obvious refactoring opportunities like:

```python
# setup.py — flagged
def setup_gitignore():
    gitignore = project / ".gitignore"  # ← line 1
    gitignore.write_text("__pycache__\n")

def setup_editorconfig():
    gitignore = project / ".gitignore"  # ← line 2
    gitignore.unlink(missing_ok=True)

def setup_readme():
    gitignore = project / ".gitignore"  # ← line 3, flagged: extract module-level constant
    gitignore.touch()
```

**What it skips (intentional false negatives):**

| Pattern | Example | Why |
|---|---|---|
| Function calls | `data = parse_config()` | Cannot infer purity from text |
| Subscripts | `value = config["key"]` | Often legitimate per-call lookup |
| Container literals | `findings = []`, `headers = {}` | Each instance is a fresh local |
| Object construction | `mock = MagicMock(...)` | New object per call |
| Annotated assignments | `count: int = 5` | Likely declaration, not derivation |
| Trailing-comma lines | `value = X,` | Function arguments / multi-line calls |
| Non-assignments | `assert ...`, `if ...`, function defs | Not a value derivation |

The trade-off is conservative — false negatives are preferred over false positives. For cross-file duplicate detection (production code), use `check-duplicate` (pylint R0801).

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

**All `check-all` commands — with permanent install and with uvx:**

```bash
# run all checkers
check-all .
uvx --from git+https://github.com/lipex360x/dev-quality check-all .

# run without cache
check-all --no-cache .
uvx --from git+https://github.com/lipex360x/dev-quality check-all --no-cache .

# clear the cache
check-all --clear-cache
uvx --from git+https://github.com/lipex360x/dev-quality check-all --clear-cache

# install the AI assistant skill
check-all install-skill --target ~/.claude/skills
uvx --from git+https://github.com/lipex360x/dev-quality check-all install-skill --target ~/.claude/skills

# update the skill in-place (uses the path saved during the last install)
install-skill
uvx --from git+https://github.com/lipex360x/dev-quality install-skill
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## AI assistant skill

Install the bundled skill file so your AI assistant can apply dev-quality rules while writing code — preventing violations before the commit runs:

```bash
# Claude Code — first install
check-all install-skill --target ~/.claude/skills

# Claude Code — uvx (no install required)
uvx --from git+https://github.com/lipex360x/dev-quality check-all install-skill --target ~/.claude/skills

# Any other tool — point to its skills directory
check-all install-skill --target <your-tool-skills-dir>
```

After installation the target path is saved to `~/.config/dev-quality/skill_path`. Subsequent updates only need:

```bash
# Update in-place — no --target needed
install-skill
uvx --from git+https://github.com/lipex360x/dev-quality install-skill
```

After installation, invoke `/dev-quality` in any session to load the rules.

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Local configuration — `.dev-quality.yaml`

Create a `.dev-quality.yaml` at the project root to customize `check-all` behavior. The file is optional — all defaults apply when it is absent.

| Key | Default | Description |
|---|---|---|
| `skip` | `[]` | Checkers to disable. Valid values: `check-abbrev`, `check-comments`, `check-noqa`, `check-repeated`, `check-size`, `check-complexity`, `check-bash-tests`, `check-bash-logs`, `ruff`, `mypy`, `vulture`, `bandit`, `pylint`, `check-duplicate`, `shellcheck`, `semgrep` |
| `line_length` | `120` | Maximum line length passed to ruff |
| `max_complexity` | `6` | Maximum cyclomatic complexity for Bash functions |
| `max_file_lines` | `800` | Maximum number of lines per file |
| `max_test_file_lines` | `1500` | Maximum number of lines per test file |
| `max_func_lines` | `100` | Maximum number of lines per function |
| `python_version` | `"3.11"` | Python version passed to mypy |
| `abbrev_min_length` | `2` | Flag identifiers with this many characters or fewer (set to `0` to use denylist only) |
| `abbrev_allowlist` | `[]` | Extra identifiers to allow in addition to the built-in defaults |
| `min_duplicate_lines` | `6` | Minimum lines of similarity to flag as duplicate (Python only, `check-duplicate`) |
| `max_line_repetitions` | `2` | A non-trivial line may appear at most this many times in a single file (`check-repeated`) |
| `min_line_length` | `20` | Lines shorter than this are ignored by `check-repeated` |

```yaml
skip:
  - check-bash-logs
  - check-bash-tests

line_length: 100
max_complexity: 6
max_file_lines: 800
max_test_file_lines: 1500
max_func_lines: 100
python_version: "3.11"
abbrev_min_length: 2
abbrev_allowlist:
  - py
  - sh
```

<div align="right"><a href="#dev-quality">↑ Back to top</a></div>

---

## Individual hooks

To use specific checkers instead of `check-all`:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.15.0
    hooks:
      - id: check-abbrev
      - id: check-comments
      - id: check-noqa
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
