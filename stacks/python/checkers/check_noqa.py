from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path

_SUPPRESSION = re.compile(r"#\s*(noqa|nosec)\b")


def check_file(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return []
    findings: list[str] = []
    for token_type, token_string, token_start, _, _ in tokens:
        if token_type != tokenize.COMMENT:
            continue
        if _SUPPRESSION.search(token_string):
            line_number = token_start[0]
            findings.append(f"NOQA:{path}:{line_number}:{token_string.strip()}")
    return findings


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    findings: list[str] = []
    for file_path in files:
        findings.extend(check_file(file_path))
    for finding in findings:
        print(finding)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
