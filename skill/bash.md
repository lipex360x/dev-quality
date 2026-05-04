# dev-quality — Bash rules

Applies to `.sh` files only. General rules (TDD, abbreviations, comments, size limits) are in `./SKILL.md`.

---

## Abbreviation allowlist (Bash additions)

In addition to the core allowlist (`SKILL.md`), these are always permitted in Bash:

`dest`

---

## Comment exceptions (Bash)

In addition to shebangs, these are the only allowed comments in `.sh` files:

| Allowed | Example |
|---------|---------|
| Shellcheck directives | `# shellcheck source=/dev/null` |

---

## Complexity

Maximum cyclomatic complexity per function: **6** (default; override with `max_complexity` in `.dev-quality.yaml`).

Reduce complexity by:
- Extracting nested conditions into named helper functions
- Replacing `if/elif` chains with `case` statements
- Keeping each function to one decision path

---

## Test pairing

Every `.sh` outside `hooks/` and `tests/` must have a paired test file.

```
scripts/deploy.sh       → tests/deploy.test.sh
scripts/setup.sh        → tests/setup.test.sh
```

Create the test file before the script file (TDD).

---

## Log initialisation

Every `.sh` outside `hooks/`, `tests/`, and `lib/` must call `log::init_script` near the top of the file.

---

## Bash self-audit

In addition to the Core self-audit (`SKILL.md`):

5. Every new Bash script has a paired test file.
6. Every new Bash script calls `log::init_script`.
