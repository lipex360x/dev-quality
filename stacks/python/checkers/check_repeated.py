from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

_TRIVIAL_RE = re.compile(
    r"^[\)\]\}]+,?$"
    r"|^(pass|continue|break)$"
    r"|^return(\s+(None|True|False))?$"
    r"|^(else|try|finally):$"
    r"|^except[^:]*:$"
    r"|^(done|fi|esac)$"
)


def _get_max_repetitions() -> int:
    return int(os.environ.get("CHECK_REPEATED_MAX_REPETITIONS", "2"))


def _get_min_line_length() -> int:
    return int(os.environ.get("CHECK_REPEATED_MIN_LINE_LENGTH", "20"))


def _update_block(line: str, in_block: str | None) -> tuple[bool, str | None]:
    if in_block is not None:
        if in_block in line:
            return True, None
        return True, in_block
    for quote in ('"""', "'''"):
        if quote in line:
            rest = line[line.index(quote) + 3 :]
            if quote in rest:
                return True, None
            return True, quote
    return False, None


def _collect_docstring_lines(lines: list[str]) -> frozenset[int]:
    result: set[int] = set()
    in_block: str | None = None
    for lineno, line in enumerate(lines, start=1):
        is_docstring, in_block = _update_block(line, in_block)
        if is_docstring:
            result.add(lineno)
    return frozenset(result)


def _should_skip(stripped: str, min_len: int) -> bool:
    if not stripped:
        return True
    if len(stripped) < min_len:
        return True
    if stripped.startswith(("#", "@")):
        return True
    return bool(_TRIVIAL_RE.match(stripped))


def _count_occurrences(lines: list[str], docstring_lines: frozenset[int], min_len: int) -> dict[str, list[int]]:
    occurrences: defaultdict[str, list[int]] = defaultdict(list)
    for lineno, line in enumerate(lines, start=1):
        if lineno in docstring_lines:
            continue
        if _should_skip(line.strip(), min_len):
            continue
        occurrences[line.strip()].append(lineno)
    return dict(occurrences)


def check_file(path: Path) -> list[str]:
    max_reps = _get_max_repetitions()
    min_len = _get_min_line_length()

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"PARSE_ERROR:{path}:{error}"]

    lines = raw.splitlines()
    docstring_lines = _collect_docstring_lines(lines) if path.suffix == ".py" else frozenset()
    occurrences = _count_occurrences(lines, docstring_lines, min_len)

    findings: list[str] = []
    for content, line_numbers in sorted(occurrences.items(), key=lambda item: item[1][0]):
        if len(line_numbers) > max_reps:
            line_list = ",".join(str(number) for number in line_numbers)
            findings.append(f"REPEATED:{path}:{line_list}:{content}")

    return findings


def main() -> None:
    files = [Path(argument) for argument in sys.argv[1:]]
    if not files:
        sys.exit(0)

    all_findings: list[str] = []
    for file_path in files:
        all_findings.extend(check_file(file_path))

    for finding in all_findings:
        print(finding)

    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
