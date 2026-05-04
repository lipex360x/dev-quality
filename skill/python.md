# dev-quality — Python rules

Applies to `.py` files only. General rules (TDD, abbreviations, comments, size limits) are in `./SKILL.md`.

---

## Ruff rules active

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

---

## mypy — strict mode

Every function needs complete type annotations:

```python
def process(items: list[str], limit: int = 10) -> list[str]:
```

No `Any` unless unavoidable. Prefer `object` for genuinely unknown types.

---

## Naming (pylint C0103)

- Variables and arguments: `snake_case`, minimum 3 characters
- Always allowed short names: `i`, `j`, `k`, `_`, `id`, `ok`
- Functions: `snake_case`, minimum 3 characters
- Classes: `PascalCase`, minimum 3 characters

---

## Semgrep

Runs automatically when the project has `.semgrep/` (directory with `.yml`/`.yaml` rules) or `semgrep.yml`/`semgrep.yaml` at the root. Silently skipped when neither exists or semgrep is not installed. Disable with `skip: [semgrep]` in `.dev-quality.yaml`.

---

## Python self-audit

In addition to the Core self-audit (`SKILL.md`):

5. All nested `with` statements are combined.
6. All imports are sorted and grouped correctly (stdlib → third-party → local).
7. All functions have complete type annotations.
8. No f-strings without placeholders.
