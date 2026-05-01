# dev-quality

Central repository for code quality tooling across stacks.

Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts.
Single source of truth — no more copying tools across projects.

---

## Checkers

| Hook | Languages | What it validates |
|---|---|---|
| `check-abbrev` | Python, Bash | Banned abbreviations (`buf`, `cfg`, `ref`, `tmp`, etc.) |
| `check-comments` | Python, Bash | Inline and block comments (except shebangs, `# shellcheck`, `# noqa`, `# type: ignore`, PEP 723 blocks) |
| `check-size` | Python, Bash | Files over 800 lines or functions over 80 lines |
| `check-complexity` | Bash | Functions with cyclomatic complexity above 6 |
| `check-bash-tests` | Bash | Every `.sh` outside `hooks/` and `tests/` must have a paired test file |
| `check-bash-logs` | Bash | Every `.sh` outside `hooks/`, `tests/` and `lib/` must call `log::init_script` |
| `ruff check` | Python | Linting: imports, style, bugs, McCabe complexity, security |
| `ruff format` | Python | Code formatting |
| `mypy` | Python | Static type checking in strict mode |
| `vulture` | Python | Dead code (unused functions and variables) |
| `bandit` | Python | Security vulnerabilities |
| `pylint C0103` | Python | Variable and function naming conventions |
| `shellcheck` | Bash | Bugs and bad practices in shell scripts |

---

## How to use

### One-off analysis — `uvx` (no install required)

Run all checkers against any project without installing anything:

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all /path/to/project
```

Useful for auditing a project before setting up pre-commit, or in CI without prior setup.

### Automated on every commit — pre-commit

Add to the target project's `.pre-commit-config.yaml` to run automatically:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.1
    hooks:
      - id: check-all
```

Then install the hooks:

```bash
pre-commit install
```

---

## Local configuration — `.dev-quality.yaml`

Create a `.dev-quality.yaml` at the project root to customize `check-all` behavior:

```yaml
# .dev-quality.yaml

# Checkers to skip (any combination of the names below)
# check-abbrev, check-comments, check-size, check-complexity,
# check-bash-tests, check-bash-logs,
# ruff, mypy, vulture, bandit, pylint, shellcheck
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

---

## Individual hooks

To use specific checkers instead of `check-all`:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.1
    hooks:
      - id: check-abbrev
      - id: check-comments
      - id: check-size
      - id: check-complexity
      - id: check-bash-tests
      - id: check-bash-logs
```

> Individual hooks do not include ruff, mypy, vulture, bandit, pylint, and shellcheck.
> Use `check-all` to run the full suite.

---

## Stacks

| Stack | Status |
|---|---|
| Python | in progress |
| Bash | in progress |
| TypeScript | planned |

---

## Reference

Tooling decisions are documented in the [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint).
This repo is the implementation — the blueprint is the spec.
