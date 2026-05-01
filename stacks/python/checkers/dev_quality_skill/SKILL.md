---
name: dev-quality
description: >-
  Rules enforced by dev-quality checkers. Use this skill in any project that
  runs dev-quality so Claude produces code that passes all checks on the first
  commit — no post-write refactor needed.
user-invocable: true
allowed-tools:
  - Read
  - Bash
---

# dev-quality — coding rules

This project runs dev-quality on every commit. The rules below are what the
checkers enforce. Follow them while writing — not after.

## Commands

### check-all

Runs the full checker suite against a directory.

| Invocation | What it does |
|---|---|
| `check-all .` | Run all checkers against the current directory |
| `check-all /path/to/project` | Run against a specific path |
| `check-all --no-cache .` | Run without ruff/mypy cache (slower, no state written) |
| `check-all --clear-cache` | Delete the cache at `/tmp/dev-quality/` and exit |

### Individual file checkers

Accept one or more file paths. Run automatically by `check-all`.

| Command | What it checks |
|---|---|
| `check-abbrev <files>` | Banned abbreviations in identifiers |
| `check-comments <files>` | Inline and block comments |
| `check-size <files>` | File and function line limits |
| `check-complexity <files>` | Cyclomatic complexity of Bash functions |

### Directory checkers

Accept a project root. Run automatically by `check-all`.

| Command | What it checks |
|---|---|
| `check-bash-tests <root>` | Every `.sh` outside `hooks/` and `tests/` has a paired test |
| `check-bash-logs <root>` | Every `.sh` outside `hooks/`, `tests/`, and `lib/` calls `log::init_script` |

### Skill installer

| Invocation | What it does |
|---|---|
| `install-skill` | Copy `SKILL.md` to `~/.claude/skills/dev-quality/` |
| `install-skill --target <dir>` | Copy to a custom skills directory |

---

## Active limits

The defaults below apply unconditionally. If `.dev-quality.yaml` exists at
the project root, read it and use those values instead — but when it is absent,
the defaults are already in effect; no file needed.

| Limit | Default |
|-------|---------|
| Lines per file | 800 |
| Lines per function | 100 |
| Cyclomatic complexity (Bash) | 6 |
| Line length | 100 |

## Banned abbreviations

Never use these as identifiers (variable names, function names, parameters,
local variables) in `.py` or `.sh` files:

| Abbreviation | Use instead |
|---|---|
| `attr` | `attribute` |
| `buf` | `buffer` |
| `cfg` | `config` or `configuration` |
| `cmd` | `command` |
| `col` | `column` or `color` |
| `ctx` | `context` |
| `db` | `database` |
| `dest` | `destination` |
| `doc` | `document` |
| `dst` | `destination` |
| `elem` | `element` |
| `env` | `environment` |
| `err` | `error` |
| `exc` | `exception` |
| `ext` | `extension` |
| `fmt` | `format` |
| `fn` | `function` |
| `func` | `function` |
| `idx` | `index` |
| `img` | `image` |
| `mod` | `module` |
| `msg` | `message` |
| `num` | `number` |
| `obj` | `object` |
| `opts` | `options` |
| `pkg` | `package` |
| `ref` | `reference` |
| `req` | `request` |
| `res` | `response` or `result` |
| `sep` | `separator` |
| `src` | `source` |
| `tmp` | `temporary` |
| `usr` | `user` |
| `val` | `value` |
| `var` | `variable` |

**Always allowed:** `self`, `cls`, `args`, `kwargs`, `i`, `j`, `k`, `_`, `id`, `ok`, `io`.

In Bash only, `dest` is also allowed (counterpart to `src` in file-operation functions).

## Comments

No comments in `.py` or `.sh` files. The only exceptions:

| Allowed | Example |
|---------|---------|
| Shebang | `#!/usr/bin/env bash` |
| Shellcheck directives | `# shellcheck source=/dev/null` |
| Ruff suppressions | `# noqa: S603` |
| Mypy suppressions | `# type: ignore[attr-defined]` |
| Coverage exclusions | `# pragma: no cover` |
| PEP 723 script blocks | `# /// script` … `# ///` |

If you feel like writing a comment, rename the variable or extract a function instead.

Size limits apply to both `.py` and `.sh`. Empty lines count toward the total.
If a function is approaching the limit, split it before finishing — extracting
a helper after the fact is more disruptive than designing for it upfront.

## Python — ruff rules active

| Set | What it checks |
|-----|----------------|
| `E`, `F` | PEP 8 style and undefined names |
| `I` | Import sorting |
| `UP` | Modernise syntax (f-strings, union types, etc.) |
| `B` | Bugbear — likely bugs and bad practices |
| `SIM` | Simplifiable code |
| `RET` | Return statement cleanup |
| `C` | McCabe complexity |
| `S` | Security — S101/S603/S607 suppressed in test files |
| `N` | Naming conventions |
| `PLR2004` | Magic number comparisons — suppressed in test files |

**Patterns that trigger violations while writing:**

- Nested `with` statements → combine: `with A(), B():` not `with A():\n    with B():`
- f-strings without placeholders → `"text"` not `f"text"`
- Unsorted imports → stdlib first, then third-party, then local; alphabetical within each group
- Mutable defaults → `def f(items: list[str] | None = None)` not `def f(items: list[str] = [])`

## Python — mypy strict

Every function needs complete type annotations:

```python
def process(items: list[str], limit: int = 10) -> list[str]:
```

No `Any` unless unavoidable. Prefer `object` for genuinely unknown types.

## Python — naming (pylint C0103)

- Variables and arguments: `snake_case`, minimum 3 characters
- Always allowed short names: `i`, `j`, `k`, `_`, `id`, `ok`
- Functions: `snake_case`, minimum 3 characters
- Classes: `PascalCase`, minimum 3 characters

## Bash — complexity

Maximum cyclomatic complexity per function: **6** (default, see `max_complexity`).

Reduce complexity by extracting nested conditions into named helpers, replacing
`if/elif` chains with `case` statements, and keeping each function to one
decision path.

## Bash — test pairing

Every `.sh` outside `hooks/` and `tests/` must have a paired test file.
Create `tests/deploy.test.sh` when you create `scripts/deploy.sh`.

## Bash — log initialisation

Every `.sh` outside `hooks/`, `tests/`, and `lib/` must call `log::init_script`
near the top of the file.

## Local overrides (optional)

If `.dev-quality.yaml` exists at the project root, it overrides the defaults
from the "Active limits" table above. Read it before starting any task.

```yaml
max_file_lines: 1000   # overrides 800
max_func_lines: 120    # overrides 100
max_complexity: 8      # overrides 6
line_length: 120       # overrides 100
python_version: "3.12"
skip:
  - check-bash-logs
```

If the file does not exist — including when running via `uvx` — the defaults apply as-is.

## Self-audit before finishing

Before reporting a task as done:

1. No banned abbreviations used as identifiers
2. No comments written (except the allowed exceptions)
3. No function exceeds the active `max_func_lines` limit (100 unless overridden)
4. No file exceeds the active `max_file_lines` limit (800 unless overridden)
5. All nested `with` statements are combined
6. All imports are sorted and grouped correctly
7. All functions have complete type annotations (Python)
8. No f-strings without placeholders
9. Every new Bash script has a paired test and calls `log::init_script`
