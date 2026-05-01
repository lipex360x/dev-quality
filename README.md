# dev-quality

Central repository for code quality tooling across stacks.

Houses custom checker scripts, pre-commit hook definitions, and bootstrap scripts.
Single source of truth — no more copying tools across projects.

---

## Checkers

| Hook | Linguagens | O que valida |
|---|---|---|
| `check-abbrev` | Python, Bash | Nomes abreviados proibidos (`buf`, `cfg`, `ref`, `tmp`, etc.) |
| `check-comments` | Python, Bash | Comentários inline ou de bloco (exceto shebangs, `# shellcheck`, `# noqa`, `# type: ignore`, blocos PEP 723) |
| `check-size` | Python, Bash | Arquivo acima de 800 linhas ou função acima de 80 linhas |
| `check-complexity` | Bash | Complexidade ciclomática de funções acima de 6 |
| `check-bash-tests` | Bash | Todo `.sh` fora de `hooks/` e `tests/` precisa de teste pareado em `scripts/bash/tests/` |
| `check-bash-logs` | Bash | Todo `.sh` fora de `hooks/`, `tests/` e `lib/` precisa chamar `log::init_script` |

---

## Rodar tudo em um projeto

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all /caminho/do/projeto
```

Ou para o diretório atual:

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all .
```

---

## Stacks

| Stack | Status |
|---|---|
| Python | in progress |
| Bash | planned |
| TypeScript | planned |

---

## Consumir via pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.0
    hooks:
      - id: check-abbrev
      - id: check-comments
      - id: check-size
      - id: check-complexity
      - id: check-bash-tests
      - id: check-bash-logs
```

---

## Bootstrap de um novo projeto

```bash
uv run https://raw.githubusercontent.com/lipex360x/dev-quality/main/bootstrap.py --stack python
```

---

## Referência

Decisões de tooling documentadas no [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint).
Este repo é a implementação — o blueprint é a especificação.
