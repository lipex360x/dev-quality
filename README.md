# dev-quality

Central repository for code quality tooling across stacks.

Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts.
Single source of truth — no more copying tools across projects.

## Stacks

| Stack | Status |
|---|---|
| Python | in progress |
| Bash | planned |
| TypeScript | planned |

## How other projects consume this

### Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.0
    hooks:
      - id: check-abbrev
      - id: check-comments
```

### Bootstrap a new project

```bash
uv run https://raw.githubusercontent.com/lipex360x/dev-quality/main/bootstrap.py --stack python
```

## Reference

Tooling decisions are documented in [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint).
This repo is the implementation — the blueprint is the spec.
