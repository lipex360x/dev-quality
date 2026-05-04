---
name: dev-quality
description: >-
  Rules enforced by dev-quality checkers. Apply while writing code so it passes
  all checks on the first commit — no post-write refactor needed.
  Language-specific rules: ./python.md (Python), ./bash.md (Bash).
---

# dev-quality — coding rules

## Commands

Run all checkers against a directory:

| Invocation | What it does |
|---|---|
| `check-all .` | Run all checkers against the current directory |
| `check-all /path/to/project` | Run against a specific path |
| `check-all --no-cache .` | Run without ruff/mypy cache |
| `check-all --clear-cache` | Delete the cache at `/tmp/dev-quality/` and exit |

Individual file checkers (accept one or more file paths):

| Command | What it checks |
|---|---|
| `check-abbrev <files>` | Abbreviations in identifiers (denylist + short-name detection) |
| `check-comments <files>` | Inline and block comments |
| `check-noqa <files>` | Inline `# noqa` and `# nosec` annotations |
| `check-size <files>` | File and function line limits |
| `check-complexity <files>` | Cyclomatic complexity of Bash functions |

Directory checkers (accept a project root):

| Command | What it checks |
|---|---|
| `check-bash-tests <root>` | Every `.sh` outside `hooks/` and `tests/` has a paired test |
| `check-bash-logs <root>` | Every `.sh` outside `hooks/`, `tests/`, and `lib/` calls `log::init_script` |

Skill installer:

| Invocation | What it does |
|---|---|
| `check-all install-skill --target <dir>` | Install skill files to `<dir>/dev-quality/` and save the path |
| `install-skill --target <dir>` | Same via the standalone command |
| `install-skill` | Update in-place — uses the path saved during the last install |

---

## Active limits

Defaults apply unconditionally. If `.dev-quality.yaml` exists at the project root, its values take precedence.

| Limit | Default |
|-------|---------|
| Lines per file | 800 |
| Lines per test file | 1500 |
| Lines per function | 100 |
| Cyclomatic complexity (Bash) | 6 |
| Line length | 100 |

---

## Abbreviation rules

Two complementary rules run together:

1. **Short-name detection** — any identifier with ≤ 2 characters is flagged unless it is in the allowlist.
2. **Denylist** — specific abbreviations are always flagged regardless of length.

Both rules apply to variable names, function names, parameters, and local variables in all supported languages.

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

- `i`, `j`, `k` — numeric loop counters only, not abbreviations for the item being iterated.
- `id` — database/object identifier convention.
- `ok` — a complete word, not an abbreviation.

In Bash only, `dest` is also allowed.

### Loop variables

Loop variables are **not exempt**. Use the full element name:

```python
for finding in findings:   # correct
for f in findings:         # ABBREV
```

```bash
for candidate in "${candidates[@]}"; do   # correct
for c in "${candidates[@]}"; do           # ABBREV
done
```

---

## Comments

No comments in source files. The only exceptions:

| Allowed | Example |
|---------|---------|
| Shebang | `#!/usr/bin/env bash` |
| Shellcheck directives | `# shellcheck source=/dev/null` |
| Type-checker suppressions | `# type: ignore[attr-defined]` |
| Coverage exclusions | `# pragma: no cover` |
| PEP 723 script blocks | `# /// script` … `# ///` |

**`# noqa` and `# nosec` are not allowed inline.** If a linter rule fires on unavoidable code, add it to `per-file-ignores` in the project's config file instead.

If you feel like writing a comment, rename the variable or extract a function instead.

---

## Local overrides (optional)

If `.dev-quality.yaml` exists at the project root, it overrides the defaults above.

```yaml
max_file_lines: 1000
max_test_file_lines: 2000
max_func_lines: 120
max_complexity: 8
line_length: 120
abbrev_min_length: 3
abbrev_allowlist:
  - ok
  - py
  - sh
skip:
  - check-bash-logs
```

`abbrev_allowlist` adds identifiers on top of the built-in allowlist — it does not replace it.

---

## TDD — non-negotiable

**Red → Green → Refactor. No exceptions.**

1. Write the test first.
2. Run it — it **must fail** (red). If it passes without implementation, the test is wrong.
3. Write the minimum implementation to make it pass (green).
4. Refactor if needed, keeping tests green.

Every bug fix starts with a failing test that reproduces the bug before touching any implementation.

Coverage must reach 100% — checkers are small enough to cover fully.

---

## Self-audit before finishing

Before reporting a task as done:

1. No banned abbreviations; no identifiers with ≤ 2 chars unless in the allowlist.
2. No comments (except the allowed exceptions listed above).
3. No function exceeds the active `max_func_lines` limit.
4. No file exceeds the active limit (`max_file_lines` for production, `max_test_file_lines` for test files).

For language-specific self-audit items, see `./python.md` or `./bash.md`.
