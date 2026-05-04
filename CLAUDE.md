# dev-quality

Central repository for code quality tooling. Houses custom checker scripts,
pre-commit hook definitions, and bootstrap scripts for all stacks.

This repo is the **implementation**. The [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint)
is the **spec** — consult it for decisions, tool categories, and rationale.
The `.brain` project (`~/www/claude/.brain`) is the most up-to-date reference
for conventions currently in use.

---

## Purpose

Eliminate manual copying of quality tooling across projects.
Other projects reference this repo — they never own a copy of the checkers.

---

## Architecture

```
stacks/
  python/
    checkers/       ← standalone checker scripts (no framework deps beyond stdlib + yaml)
    README.md       ← manual setup instructions for Python stack
  bash/
    README.md
  typescript/
    README.md
shared/
  abbrev-rules.yaml ← cross-stack banned abbreviations
bootstrap.py        ← uv run entry point: bootstraps quality pipeline in a target project
.pre-commit-hooks.yaml ← all hook definitions consumed by other projects
pyproject.toml      ← config for running checkers and tests in this repo itself
```

---

## How other projects consume this

**Pre-commit (reference by tag):**
```yaml
- repo: https://github.com/lipex360x/dev-quality
  rev: v0.1.0
  hooks:
    - id: check-abbrev
    - id: check-comments
```

**Bootstrap a new project (one command):**
```bash
uv run https://raw.githubusercontent.com/lipex360x/dev-quality/main/bootstrap.py --stack python
```

The bootstrap script writes `pyproject.toml`, `.pre-commit-config.yaml`, and
the directory structure — then prints the manual steps for anything it can't do
programmatically.

---

## Stacks

| Stack | Status | Checkers |
|---|---|---|
| Python | in progress | check_abbrev, check_comments, check_complexity, check_size, check_bash_tests, check_bash_logs |
| Bash | in progress | check_abbrev, check_comments, check_complexity, check_size, check_bash_tests, check_bash_logs, shellcheck |
| TypeScript | planned | — |

---

## Adding a new stack

1. Create `stacks/<name>/` with a `README.md` documenting manual setup
2. Add checker scripts to `stacks/<name>/checkers/` if needed
3. Register hooks in `.pre-commit-hooks.yaml`
4. Add bootstrap support in `bootstrap.py`
5. Update the stack table above

---

## Testing as a user

When asked to test or validate behavior as a user would, always use `uvx` fetching
from the published GitHub tag — never `uv run`:

```bash
cd /path/to/target-project
uvx --from git+https://github.com/lipex360x/dev-quality check-all .
```

`uv run` uses the local source and bypasses the published package. `uvx` is what
real users run.

---

## Key rules in this repo

- **TDD**: test file first, implementation second. No exceptions.
- **No comments** in `.py` and `.sh` files (shebangs, `# noqa`, `# type: ignore`, `# pragma: no cover` allowed).
- **No abbreviations**: reads `shared/abbrev-rules.yaml`.
- **Coverage**: 100% — checkers are small enough to cover fully.
- Individual checkers (`check_abbrev`, `check_comments`, etc.) are **standalone**: only stdlib + `pyyaml`.
- `check_all` orchestrates all tools and depends on ruff, mypy, bandit, vulture, pylint, shellcheck-py.

---

## Versioning

After every commit to this repo, bump the version and tag the release.

**Where to update:** `pyproject.toml` → `[project] version`

**Then release using the script:**
```bash
uv run release.py --dry-run  # preview first
uv run release.py            # creates tag, pushes, creates GitHub Release
```

CHANGELOG is the **source of truth** for the version. The script reads the top entry,
updates `pyproject.toml` and the README badge automatically, and commits those changes.
Never update `pyproject.toml` or the README badge manually — `release.py` handles both.
Never use manual `git tag` / `git push` / `gh release create` — always use the script.

**On every behavior-changing commit:**
1. `CHANGELOG.md` → add entry under the new version (this sets the version)
2. `stacks/python/checkers/dev_quality_skill/SKILL.md` → reflect any new or changed rule. The skill is layered (see below) — update the right layer:
   - **Core layer** (top of the file, language-agnostic) for changes to: TDD, abbreviations, comments, size limits, `.dev-quality.yaml`, self-audit, install/update flow, commands. These rules apply to every language.
   - **Language layer** (`## Python`, `## Bash`, `## TypeScript`, `## Java`, ...) for changes that only apply to one language: linter rules, type-checker conventions, naming patterns, language-specific tooling.
   - **Adding a new language** → add a new top-level section at the bottom of the file. Do not duplicate Core rules in the language section — the language section only carries what is genuinely specific.
3. `README.md` → update any user-facing sections affected by the change (new commands, new config keys, updated defaults, new workflows, new languages). README must always reflect the current behavior — never leave it out of sync.
4. Commit
5. `uv run release.py --release` → reads version from CHANGELOG, updates `pyproject.toml` + README badge, commits those, creates tag, pushes, creates GitHub Release

**The skill is consumed by multiple AI assistants — not just Claude.** The `install-skill` command exists precisely because users install it into whatever skills directory their tool uses (Claude Code, Cursor, Continue, custom). Therefore:
- `SKILL.md` frontmatter must use only portable fields (`name`, `description`) — no `allowed-tools`, `user-invocable`, or other Claude-specific keys
- The body must be tool-neutral — no "Claude does X", no slash-command references, no tool-specific tool names. Use imperative voice or "the AI assistant" when a subject is unavoidable.
- When in doubt, ask: "would a non-Claude tool that loaded this file still understand it?" — if no, rewrite.

**For documentation-only commits** (README prose, CLAUDE.md, guides): commit + `git push`, do **not** run `release.py`.

Always push after every commit — behavior-changing or docs-only.

**Two modes:**
- `uv run release.py` — updates `pyproject.toml` + README badge + commits, no tag/release
- `uv run release.py --release` — same as above, then creates tag + GitHub Release
- `uv run release.py --dry-run` — preview only, no git operations

**Only tag when the package behavior changes** — new checker, bug fix that affects output, new config param, new command, new hook. Do NOT tag for docs, CLAUDE.md updates, status changes, or test-only commits.

**Semver rules — choose based on what was committed:**

| Change | Bump |
|---|---|
| Bug fix, behavior correction | `patch` — `v0.1.x` |
| New checker, new config param, new command, new hook | `minor` — `v0.x.0` |
| Breaking change: hook renamed/removed, config key renamed, checker output format changed | `major` — `vx.0.0` |

Always push the tag immediately after the version bump commit. Never batch multiple features under a single tag bump.

---

## Current status (2026-05-01)

- [x] Python stack checkers migrated from `.brain`
- [x] `shared/abbrev-rules.yaml` populated
- [x] `.pre-commit-hooks.yaml` defined
- [x] `pyproject.toml` configured
- [x] First release tagged (`v0.1.1`)
- [ ] `bootstrap.py` implemented
- [ ] `netbeans-setup` consuming this repo via pre-commit
