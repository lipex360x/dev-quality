from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

_DEFAULT_DENYLIST: frozenset[str] = frozenset([
    "attr", "buf", "cfg", "cmd", "col", "ctx", "db", "dest", "doc", "dst",
    "elem", "env", "err", "exc", "ext", "fmt", "fn", "func", "idx", "img",
    "mod", "msg", "num", "obj", "opts", "pkg", "ref", "req", "res", "sep",
    "src", "tmp", "usr", "val", "var",
])
_DEFAULT_ALLOWLIST: frozenset[str] = frozenset([
    "self", "cls", "args", "kwargs", "i", "j", "k", "_", "id", "ok", "io",
])
_DEFAULT_LANG: dict[str, frozenset[str]] = {"sh": frozenset(["dest"])}


def _find_rules_file() -> Path | None:
    candidates = [
        Path(sys.argv[0]).parent.parent.parent / "shared" / "abbrev-rules.yaml",
        Path(__file__).parent.parent.parent.parent / "shared" / "abbrev-rules.yaml",
    ]
    return next((p for p in candidates if p.exists()), None)


def _load_rules(
    path: Path | None = None,
) -> tuple[frozenset[str], frozenset[str], dict[str, frozenset[str]]]:
    resolved = path if path is not None else _find_rules_file()
    if resolved is None or not resolved.exists():
        return _DEFAULT_DENYLIST, _DEFAULT_ALLOWLIST, _DEFAULT_LANG
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    denylist = frozenset(data.get("denylist", []))
    allowlist = frozenset(data.get("allowlist", []))
    lang_allowlists: dict[str, frozenset[str]] = {
        key.removeprefix("allowlist_"): frozenset(data.get(key, []))
        for key in data
        if key.startswith("allowlist_") and key != "allowlist"
    }
    return denylist, allowlist, lang_allowlists


def _flag(findings: list[str], path: Path, line: int, name: str) -> None:
    findings.append(f"ABBREV:{path}:{line}:{name}")


_FUNC_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _node_identifier(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return node.id
    if isinstance(node, ast.arg):
        return node.arg
    if isinstance(node, ast.ExceptHandler) and node.name:
        return node.name
    if isinstance(node, _FUNC_DEF_NODES):
        return node.name
    return None


def _check_file(path: Path, denylist: frozenset[str], allowlist: frozenset[str]) -> list[str]:
    findings: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, OSError, UnicodeDecodeError) as parse_error:
        return [f"PARSE_ERROR:{path}:{parse_error}"]
    for node in ast.walk(tree):
        name = _node_identifier(node)
        if name is not None and name not in allowlist and name in denylist:
            _flag(findings, path, node.lineno, name)  # type: ignore[attr-defined]
    return findings


_BASH_VAR_RE = re.compile(
    r"(?:"
    r"(?:local|readonly|declare(?:\s+-[a-zA-Z]+)*)\s+"
    r"([a-zA-Z_][a-zA-Z0-9_]*)(?:=|\s|$)"
    r"|for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in"
    r"|function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    r"|^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)"
    r")"
)

_BASH_PLAIN_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)=")


def _check_bash_line(
    stripped: str,
    path: Path,
    lineno: int,
    denylist: frozenset[str],
    effective_allowlist: frozenset[str],
    findings: list[str],
) -> None:
    plain_match = _BASH_PLAIN_RE.match(stripped)
    if plain_match:
        name = plain_match.group(1)
        if name not in effective_allowlist and name in denylist:
            _flag(findings, path, lineno, name)
        return
    for match in _BASH_VAR_RE.finditer(stripped):
        name = next(g for g in match.groups() if g is not None)
        if name not in effective_allowlist and name in denylist:
            _flag(findings, path, lineno, name)


def _check_bash_file(
    path: Path,
    denylist: frozenset[str],
    allowlist: frozenset[str],
    lang_allowlists: dict[str, frozenset[str]] | None = None,
) -> list[str]:
    effective_allowlist = allowlist | (lang_allowlists or {}).get("sh", frozenset())
    findings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as read_error:
        return [f"PARSE_ERROR:{path}:{read_error}"]
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        _check_bash_line(stripped, path, lineno, denylist, effective_allowlist, findings)
    return findings


def _scan_file(
    file_path: Path,
    denylist: frozenset[str],
    allowlist: frozenset[str],
    lang_allowlists: dict[str, frozenset[str]],
) -> list[str]:
    if file_path.suffix == ".sh":
        return _check_bash_file(file_path, denylist, allowlist, lang_allowlists)
    return _check_file(file_path, denylist, allowlist)


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    if not files:
        sys.exit(0)
    denylist, allowlist, lang_allowlists = _load_rules()
    all_findings: list[str] = []
    for file_path in files:
        all_findings.extend(_scan_file(file_path, denylist, allowlist, lang_allowlists))
    for finding in all_findings:
        print(finding)
    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
