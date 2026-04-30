# Python Stack

Quality pipeline for Python 3.11+ projects using `uv`.

---

## Tools

| Tool | What it does | Config |
|---|---|---|
| `ruff format` | Formatter | `pyproject.toml [tool.ruff]` |
| `ruff check` | Linter (E F I UP B SIM RET C S N PLR2004) | `pyproject.toml [tool.ruff.lint]` |
| `mypy --strict` | Static type checking | `pyproject.toml [tool.mypy]` |
| `bandit` | Deep security scan | `pyproject.toml [tool.bandit]` |
| `vulture` | Dead code detection (≥80%) | `pyproject.toml [tool.vulture]` |
| `pylint C0103` | Naming conventions | `pyproject.toml [tool.pylint]` |
| `pylint R0801` | Duplicate code detection | `pyproject.toml [tool.pylint]` |
| `pytest + coverage` | Tests + 100% coverage | `pyproject.toml [tool.coverage]` |

## Custom checkers

| Script | What it does |
|---|---|
| `checkers/check_abbrev.py` | Blocks banned abbreviations (reads `shared/abbrev-rules.yaml`) |
| `checkers/check_comments.py` | Blocks comments in source (except shebangs, noqa, type: ignore) |
| `checkers/check_complexity.py` | Cyclomatic complexity limit (custom, beyond ruff C90) |
| `checkers/check_size.py` | File size limits per directory |
| `checkers/check_bash_tests.py` | Every `.sh` must have a paired test |
| `checkers/check_bash_logs.py` | Validates log patterns in bash scripts |

---

## Manual setup

### 1. Initialize uv project

```bash
uv init
uv python pin 3.11
```

### 2. Create pyproject.toml

Copy `stacks/python/pyproject.template.toml` and adjust `[project].name`.

Key settings:
- `line-length = 100`
- `max-complexity = 5`
- `fail_under = 95`, `branch = true`

### 3. Add dev dependencies

```bash
uv add --dev ruff mypy bandit vulture pylint pytest pytest-cov pyyaml
```

### 4. Configure pre-commit

```bash
uv tool install pre-commit
```

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.0
    hooks:
      - id: check-abbrev
      - id: check-comments
      - id: check-complexity
      - id: check-size
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        args: [--strict]
```

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

### 5. Verify

```bash
pre-commit run --all-files
uv run pytest --cov
```

---

## pyproject.toml reference settings

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RET", "C", "S", "N", "PLR2004"]

[tool.ruff.lint.mccabe]
max-complexity = 5

[tool.mypy]
strict = true
python_version = "3.11"

[tool.coverage.run]
branch = true

[tool.coverage.report]
fail_under = 95
show_missing = true
```
