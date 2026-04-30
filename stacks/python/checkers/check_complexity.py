from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_FUNC_RE = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)|^function\s+([a-zA-Z_][a-zA-Z0-9_]*)"
)
_BRANCH_RE = re.compile(r"^\s*(if|elif|for|while|until)\b")
_CASE_BRANCH_RE = re.compile(r";;")


def _line_score(line: str) -> int:
    stripped = line.strip()
    if stripped.startswith("#"):
        return 0
    score = 1 if _BRANCH_RE.match(stripped) else 0
    score += len(_CASE_BRANCH_RE.findall(stripped))
    return score


def _report_func(
    path: Path,
    name: str,
    lineno: int,
    score: int,
    max_complexity: int,
    findings: list[str],
) -> None:
    if score > max_complexity:
        findings.append(f"COMPLEXITY:{path}:{lineno}:{name}:{score}")


def _scan_functions(
    lines: list[str], path: Path, max_complexity: int, findings: list[str]
) -> None:
    current_func: str | None = None
    current_func_line = 0
    score = 0

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        func_match = _FUNC_RE.match(stripped)
        if func_match and current_func is None:
            if stripped.count("{") > 0 and stripped.count("{") == stripped.count("}"):
                continue
            current_func = func_match.group(1) or func_match.group(2)
            current_func_line = lineno
            score = 1
        elif current_func is not None:
            if stripped == "}":
                _report_func(path, current_func, current_func_line, score, max_complexity, findings)
                current_func = None
                score = 0
            else:
                score += _line_score(line)


def _check_bash(path: Path, max_complexity: int) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [f"READ_ERROR:{path}:{error}"]
    findings: list[str] = []
    _scan_functions(lines, path, max_complexity, findings)
    return findings


def _scan_file(file_path: Path, max_complexity: int) -> list[str]:
    if file_path.suffix == ".sh":
        return _check_bash(file_path, max_complexity)
    return []


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    if not files:
        sys.exit(0)
    max_complexity = int(os.environ.get("CHECK_COMPLEXITY_MAX", "6"))
    all_findings: list[str] = []
    for file_path in files:
        all_findings.extend(_scan_file(file_path, max_complexity))
    for finding in all_findings:
        print(finding)
    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
