from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path

_PY_ALLOWED_RE = re.compile(r"^\s*#\s*(type:\s*ignore|noqa|pyright:)", re.IGNORECASE)
_BASH_SHEBANG_RE = re.compile(r"^#!")
_BASH_SHELLCHECK_RE = re.compile(r"^\s*#\s*shellcheck\b")
_PEP723_START_RE = re.compile(r"^#\s*///\s+\w+")
_PEP723_END_RE = re.compile(r"^#\s*///\s*$")


def _pep723_block_lines(source: str) -> frozenset[int]:
    in_block = False
    lines: set[int] = set()
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not in_block and _PEP723_START_RE.match(stripped):
            in_block = True
            lines.add(lineno)
        elif in_block:
            lines.add(lineno)
            if _PEP723_END_RE.match(stripped):
                in_block = False
    return frozenset(lines)


def check_python_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
        pep723 = _pep723_block_lines(source)
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, (lineno, _), _, _ in tokens:
            if (
                tok_type == tokenize.COMMENT
                and lineno not in pep723
                and not _PY_ALLOWED_RE.match(tok_string)
            ):
                findings.append(f"COMMENT:{path}:{lineno}:{tok_string}")
    except Exception as error:
        return [f"PARSE_ERROR:{path}:{error}"]
    return findings


def _is_allowed_bash_comment(stripped: str) -> bool:
    return bool(_BASH_SHEBANG_RE.match(stripped) or _BASH_SHELLCHECK_RE.match(stripped))


def check_bash_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [f"PARSE_ERROR:{path}:{error}"]

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        if _is_allowed_bash_comment(stripped):
            continue
        findings.append(f"COMMENT:{path}:{lineno}:{stripped}")

    return findings


def _scan_file(file_path: Path) -> list[str]:
    if file_path.suffix == ".sh":
        return check_bash_file(file_path)
    return check_python_file(file_path)


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    if not files:
        sys.exit(0)

    all_findings: list[str] = []
    for file_path in files:
        all_findings.extend(_scan_file(file_path))

    for finding in all_findings:
        print(finding)

    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
