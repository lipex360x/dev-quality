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
| `check-abbrev <files>` | Abbreviations in identifiers (denylist + short-name detection) |
| `check-comments <files>` | Inline and block comments |
| `check-noqa <files>` | Inline `# noqa` and `# nosec` annotations |
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
| `check-all install-skill --target <dir>` | Install `SKILL.md` to `<dir>/dev-quality/SKILL.md` and save the path |
| `install-skill --target <dir>` | Same as above via the standalone command |
| `install-skill` | Update in-place — uses the path saved during the last install (no `--target` needed) |

---

## Active limits

The defaults below apply unconditionally. If `.dev-quality.yaml` exists at
the project root, read it and use those values instead — but when it is absent,
the defaults are already in effect; no file needed.

| Limit | Default |
|-------|---------|
| Lines per file | 800 |
| Lines per test file | 1500 |
| Lines per function | 100 |
| Cyclomatic complexity (Bash) | 6 |
| Line length | 100 |

## Abbreviation rules

`check-abbrev` enforces two complementary rules:

1. **Short-name detection** — any identifier with ≤ 2 characters is flagged unless it is
   in the allowlist. This catches abbreviations like `cc`, `fn`, `db` automatically.
2. **Denylist** — specific 3-character (and longer) abbreviations are always flagged
   regardless of length.

Both rules apply to variable names, function names, parameters, and local variables in
`.py` and `.sh` files.

### Denylist

Never use these as identifiers:

| Abbreviation | Use instead |
|---|---|
| `addr` | `address` |
| `arg` | `argument` |
| `arr` | `array` |
| `attr` | `attribute` |
| `auth` | `authentication` |
| `avg` | `average` |
| `btn` | `button` |
| `buf` | `buffer` |
| `cfg` | `config` or `configuration` |
| `cmd` | `command` |
| `cnt` | `count` |
| `col` | `column` or `color` |
| `conn` | `connection` |
| `creds` | `credentials` |
| `ctx` | `context` |
| `db` | `database` |
| `desc` | `description` |
| `dest` | `destination` |
| `dir` | `directory` |
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
| `hdr` | `header` |
| `hdrs` | `headers` |
| `idx` | `index` |
| `img` | `image` |
| `impl` | `implementation` |
| `info` | `information` |
| `lst` | `list` |
| `meta` | `metadata` |
| `mod` | `module` |
| `msg` | `message` |
| `num` | `number` |
| `obj` | `object` |
| `opts` | `options` |
| `param` | `parameter` |
| `params` | `parameters` |
| `perm` | `permission` |
| `perms` | `permissions` |
| `pkg` | `package` |
| `prop` | `property` |
| `props` | `properties` |
| `pwd` | `password` |
| `qry` | `query` |
| `qty` | `quantity` |
| `rec` | `record` |
| `ref` | `reference` |
| `req` | `request` |
| `res` | `response` or `result` |
| `resp` | `response` |
| `sep` | `separator` |
| `sess` | `session` |
| `src` | `source` |
| `tbl` | `table` |
| `tkn` | `token` |
| `tmp` | `temporary` |
| `tok` | `token` |
| `uri` | `URI` |
| `url` | `URL` |
| `usr` | `user` |
| `val` | `value` |
| `var` | `variable` |

### Allowlist (always permitted regardless of length)

`self`, `cls`, `args`, `kwargs`, `i`, `j`, `k`, `_`, `id`, `ok`

- `i`, `j`, `k` are permitted as numeric loop counters only — not as abbreviations for
  the item being iterated (e.g., `for finding in findings`, not `for f in findings`).
- `id` is permitted as a database/object identifier convention.
- `ok` is a complete word, not an abbreviation.

In Bash only, `dest` is also allowed (counterpart to `src` in file-operation functions).

### Loop variables

Loop variables are **not exempt** from abbreviation rules. Use the full element name:

```python
for finding in findings:   # correct
for f in findings:         # ABBREV — f is an abbreviation of finding
```

```bash
for candidate in "${candidates[@]}"; do   # correct
for c in "${candidates[@]}"; do           # ABBREV — c is an abbreviation
done

## Comments

No comments in `.py` or `.sh` files. The only exceptions:

| Allowed | Example |
|---------|---------|
| Shebang | `#!/usr/bin/env bash` |
| Shellcheck directives | `# shellcheck source=/dev/null` |
| Mypy suppressions | `# type: ignore[attr-defined]` |
| Coverage exclusions | `# pragma: no cover` |
| PEP 723 script blocks | `# /// script` … `# ///` |

**`# noqa` and `# nosec` are not allowed inline** — blocked by `check-noqa`. If a ruff or
bandit rule fires on unavoidable code, add it to `per-file-ignores` in `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"scripts/deploy.sh" = ["S603", "S607"]
```

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
max_file_lines: 1000        # overrides 800
max_test_file_lines: 2000   # overrides 1500
max_func_lines: 120         # overrides 100
max_complexity: 8           # overrides 6
line_length: 120            # overrides 100
python_version: "3.12"
abbrev_min_length: 3        # flag names with ≤ 3 chars (default: 2)
abbrev_allowlist:           # extra identifiers to allow in this project
  - ok
  - py
  - sh
skip:
  - check-bash-logs
```

`abbrev_allowlist` adds identifiers on top of the built-in allowlist — it does not
replace it. The built-in allowlist (`self`, `cls`, `args`, `kwargs`, `i`, `j`, `k`,
`_`, `id`, `ok`) is always active.

If the file does not exist — including when running via `uvx` — the defaults apply as-is.

## TDD — non-negotiable

**Red → Green → Refactor. No exceptions.**

Never write implementation before a failing test exists. This is not a
preference — it is the only permitted workflow in this project.

### The rule

1. Write the test first
2. Run it — it **must fail** (red). If it passes without implementation, the test is wrong or the feature already exists
3. Write the minimum implementation to make it pass (green)
4. Refactor if needed, keeping tests green

If you skip step 2 and go straight to green, you have no evidence the test
actually validates the behaviour. That test is worthless.

### What counts as a test

Every `.py` file under `scripts/python/` needs a corresponding test file in
`tests/`. The test file must exist **before** the implementation file.
Coverage must reach 100% — checkers are small enough to cover fully.

### When you are tempted to skip TDD

You will be tempted when:
- The change feels "too small" to test first → it is not
- You already know what the implementation looks like → write the test first anyway
- You are fixing a bug → write a failing test that reproduces the bug before touching any implementation

**Every bug fix starts with a failing test that demonstrates the bug.**

---

## Self-audit before finishing

Before reporting a task as done:

1. No banned abbreviations used as identifiers; no identifiers with ≤ 2 chars unless in the allowlist
2. No comments written (except the allowed exceptions)
3. No function exceeds the active `max_func_lines` limit (100 unless overridden)
4. No file exceeds the active `max_file_lines` limit (800 unless overridden)
5. All nested `with` statements are combined
6. All imports are sorted and grouped correctly
7. All functions have complete type annotations (Python)
8. No f-strings without placeholders
9. Every new Bash script has a paired test and calls `log::init_script`
