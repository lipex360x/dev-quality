# Python Stack

Quality pipeline for Python 3.11+ projects using `uv`.

---

## Tools

| Tool | What it validates | Config key |
|---|---|---|
| `ruff format` | Code formatting | `[tool.ruff]` |
| `ruff check` | Linting: E F I UP B SIM RET C S N PLR2004 | `[tool.ruff.lint]` |
| `mypy --strict` | Static type checking | `[tool.mypy]` |
| `bandit` | Security vulnerabilities | `[tool.bandit]` |
| `vulture` | Dead code (≥ 80% confidence) | `[tool.vulture]` |
| `pylint C0103` | Naming conventions | `[tool.pylint]` |
| `check-abbrev` | Banned abbreviations (AST-based) | `shared/abbrev-rules.yaml` |
| `check-comments` | No inline or block comments | — |
| `check-size` | File ≤ 800 lines, function ≤ 80 lines | env vars |
| `pytest + coverage` | Tests + 100% branch coverage | `[tool.coverage]` |

> [!NOTE]
> `ruff check` suppresses S101 (`assert` used) to avoid false positives in pytest files.
> `ruff` and `mypy` run with cache disabled so no `.ruff_cache/` or `.mypy_cache/` is
> created in the target project.

---

## Custom checkers

| Script | What it does |
|---|---|
| `checkers/check_abbrev.py` | Blocks banned abbreviations via AST (Python) and regex (Bash) |
| `checkers/check_comments.py` | Blocks comments except shebangs, `# noqa`, `# type: ignore`, PEP 723 blocks |
| `checkers/check_size.py` | Enforces file and function line limits |
| `checkers/check_complexity.py` | Cyclomatic complexity for Bash functions |
| `checkers/check_bash_tests.py` | Every `.sh` must have a paired test file |
| `checkers/check_bash_logs.py` | Every `.sh` must call `log::init_script` |
| `checkers/check_all.py` | Orchestrates all of the above plus ruff, mypy, bandit, vulture, pylint, shellcheck |

---

## Manual setup

### 1. Initialize uv project

```bash
uv init
uv python pin 3.11
```

### 2. Add dev dependencies

```bash
uv add --dev ruff mypy bandit vulture pylint pytest pytest-cov pyyaml types-pyyaml
```

### 3. Configure pyproject.toml

Key settings to match the quality pipeline:

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RET", "C", "S", "N", "PLR2004"]

[tool.ruff.lint.mccabe]
max-complexity = 6

[tool.mypy]
strict = true
python_version = "3.11"
explicit_package_bases = true

[tool.coverage.run]
branch = true

[tool.coverage.report]
fail_under = 100
show_missing = true
exclude_lines = [
    "if __name__ == .__main__.:",
    "pragma: no cover",
]

[tool.bandit]
skips = ["B404", "B603", "B607"]
exclude_dirs = ["tests"]

[tool.vulture]
min_confidence = 80

[tool.pylint.messages_control]
disable = "all"
enable = ["C0103"]

[tool.pylint.basic]
argument-rgx = "^([a-z_][a-z0-9_]{2,}|[ijk_]|id|pi)$"
variable-rgx  = "^([a-z_][a-z0-9_]{2,}|[ijk_]|id|pi)$"
function-rgx  = "^([a-z_][a-zA-Z0-9_]{2,}|[ijk_]|id|pi)$"
method-rgx    = "^([a-z_][a-zA-Z0-9_]{2,}|[ijk_]|id|pi)$"
```

### 4. Configure pre-commit

```bash
uv tool install pre-commit
pre-commit install
```

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.2.1
    hooks:
      - id: check-all
```

### 5. Verify

```bash
pre-commit run --all-files
uv run pytest
```
