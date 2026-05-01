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
| `check-bash-tests` | Bash | Todo `.sh` fora de `hooks/` e `tests/` precisa de teste pareado |
| `check-bash-logs` | Bash | Todo `.sh` fora de `hooks/`, `tests/` e `lib/` precisa chamar `log::init_script` |
| `ruff check` | Python | Linting: imports, style, bugs, complexidade McCabe, segurança |
| `ruff format` | Python | Formatação fora do padrão |
| `mypy` | Python | Tipagem estática em modo strict |
| `vulture` | Python | Código morto (funções e variáveis não usadas) |
| `bandit` | Python | Vulnerabilidades de segurança |
| `pylint C0103` | Python | Nomes de variáveis e funções fora da convenção |
| `shellcheck` | Bash | Bugs e más práticas em scripts |

---

## Rodar tudo em um projeto

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all /caminho/do/projeto
```

Ou no diretório atual:

```bash
uvx --from git+https://github.com/lipex360x/dev-quality check-all .
```

---

## Configuração local — `.dev-quality.yaml`

Crie um `.dev-quality.yaml` na raiz do projeto para personalizar o comportamento do `check-all`:

```yaml
# .dev-quality.yaml

# Checkers a ignorar (qualquer combinação dos nomes abaixo)
# check-abbrev, check-comments, check-size, check-complexity,
# check-bash-tests, check-bash-logs,
# ruff, mypy, vulture, bandit, pylint, shellcheck
skip:
  - check-bash-logs
  - check-bash-tests

# Comprimento máximo de linha (padrão: 100)
line_length: 120

# Complexidade ciclomática máxima para funções Bash e Python (padrão: 6)
max_complexity: 8

# Número máximo de linhas por arquivo (padrão: 800)
max_file_lines: 1000

# Número máximo de linhas por função (padrão: 80)
max_func_lines: 100

# Versão do Python para o mypy (padrão: "3.11")
python_version: "3.12"
```

O arquivo é opcional — sem ele, os padrões acima são aplicados.

---

## Usar via pre-commit

### Hook único (roda tudo)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/lipex360x/dev-quality
    rev: v0.1.0
    hooks:
      - id: check-all
```

### Hooks individuais

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

> **Nota:** os hooks individuais não incluem ruff, mypy, vulture, bandit, pylint e shellcheck.
> Use `check-all` para rodar a suite completa.

---

## Stacks

| Stack | Status |
|---|---|
| Python | in progress |
| Bash | planned |
| TypeScript | planned |

---

## Referência

Decisões de tooling documentadas no [engineering-blueprint](https://github.com/lipex360x/engineering-blueprint).
Este repo é a implementação — o blueprint é a especificação.
