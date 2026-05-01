# Bash Stack

Quality pipeline for Bash scripts.

---

## Tools

| Tool | What it validates |
|---|---|
| `shellcheck` | Bugs, bad practices, portability issues |
| `check-abbrev` | Banned abbreviations in variable and function names |
| `check-comments` | Inline and block comments (except shebangs and `# shellcheck` directives) |
| `check-complexity` | Cyclomatic complexity of functions (default max: 6) |
| `check-size` | Files over 800 lines or functions over 80 lines |
| `check-bash-tests` | Every `.sh` outside `hooks/` and `tests/` must have a paired test file |
| `check-bash-logs` | Every `.sh` outside `hooks/`, `tests/`, and `lib/` must call `log::init_script` |

> [!NOTE]
> All bash checkers are implemented as Python scripts in `stacks/python/checkers/`.
> `shellcheck` is bundled via `shellcheck-py` — no system install required.

---

## Manual setup

### 1. Add pre-commit hook

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.2.1
    hooks:
      - id: check-all
```

`check-all` includes shellcheck and all bash checkers automatically.

### 2. Run on demand

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all /path/to/project
```

### 3. Skip bash-specific checkers

Add to `.dev-quality.yaml` at the project root:

```yaml
skip:
  - check-bash-tests
  - check-bash-logs
  - shellcheck
```

---

## Checker details

### check-complexity

Computes cyclomatic complexity by counting branching keywords (`if`, `elif`, `while`, `for`, `case`, `&&`, `||`) inside each function body. Flags functions above the configured limit.

Default max: `6`. Override via `.dev-quality.yaml`:

```yaml
max_complexity: 8
```

### check-bash-tests

Checks that every `.sh` file under `scripts/bash/` (excluding `hooks/` and `tests/` subdirectories) has a corresponding test file at `tests/bash/<name>.test.sh`.

### check-bash-logs

Checks that every `.sh` file under `scripts/bash/` (excluding `hooks/`, `tests/`, and `lib/` subdirectories) contains a call to `log::init_script`.
