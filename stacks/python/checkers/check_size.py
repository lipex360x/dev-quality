from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

_FUNC_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)|^function\s+([a-zA-Z_][a-zA-Z0-9_]*)")
_TEST_DIRS = frozenset(["tests", "test"])


def _is_test_file(path: Path) -> bool:
    name = path.name
    return (
        any(part in _TEST_DIRS for part in path.parts)
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.py")
        or name == "conftest.py"
    )


def _py_file_findings(path: Path, line_count: int, max_file: int) -> list[str]:
    if line_count > max_file:
        return [f"FILE_TOO_LONG:{path}:{line_count}"]
    return []


def _func_finding(
    node: ast.FunctionDef | ast.AsyncFunctionDef, path: Path, max_func: int
) -> str | None:
    if node.end_lineno is None:
        return None
    func_lines = node.end_lineno - node.lineno + 1
    if func_lines > max_func:
        return f"FUNC_TOO_LONG:{path}:{node.lineno}:{node.name}:{func_lines}"
    return None


def _py_func_findings(path: Path, source: str, max_func: int) -> list[str]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [f"PARSE_ERROR:{path}:{error}"]
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            finding = _func_finding(node, path, max_func)
            if finding is not None:
                findings.append(finding)
    return findings


def _check_python(path: Path, max_file: int, max_func: int) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"READ_ERROR:{path}:{error}"]
    return _py_file_findings(path, len(source.splitlines()), max_file) + _py_func_findings(
        path, source, max_func
    )


def _is_single_line_func(stripped: str) -> bool:
    return stripped.count("{") > 0 and stripped.count("{") == stripped.count("}")


def _bash_func_findings(path: Path, lines: list[str], max_func: int) -> list[str]:
    findings: list[str] = []
    current_func: str | None = None
    current_func_line = 0

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        func_match = _FUNC_RE.match(stripped)
        if func_match and current_func is None:
            if _is_single_line_func(stripped):
                continue
            current_func = func_match.group(1) or func_match.group(2)
            current_func_line = lineno
        elif current_func is not None and stripped == "}":
            func_lines = lineno - current_func_line + 1
            if func_lines > max_func:
                findings.append(
                    f"FUNC_TOO_LONG:{path}:{current_func_line}:{current_func}:{func_lines}"
                )
            current_func = None

    return findings


def _check_bash(path: Path, max_file: int, max_func: int) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [f"READ_ERROR:{path}:{error}"]
    findings: list[str] = []
    if len(lines) > max_file:
        findings.append(f"FILE_TOO_LONG:{path}:{len(lines)}")
    return findings + _bash_func_findings(path, lines, max_func)


def _scan_file(file_path: Path, max_file: int, max_func: int) -> list[str]:
    if file_path.suffix == ".sh":
        return _check_bash(file_path, max_file, max_func)
    return _check_python(file_path, max_file, max_func)


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    if not files:
        sys.exit(0)
    max_file = int(os.environ.get("CHECK_SIZE_MAX_FILE", "800"))
    max_test_file = int(os.environ.get("CHECK_SIZE_MAX_TEST_FILE", "1500"))
    max_func = int(os.environ.get("CHECK_SIZE_MAX_FUNC", "80"))
    all_findings: list[str] = []
    for file_path in files:
        effective_max = max_test_file if _is_test_file(file_path) else max_file
        all_findings.extend(_scan_file(file_path, effective_max, max_func))
    for finding in all_findings:
        print(finding)
    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
