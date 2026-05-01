from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_SKIP_DIRS = frozenset(["__pycache__", ".venv", ".git", "node_modules"])

_CUSTOM_FILE_CHECKERS = [
    "check-abbrev",
    "check-comments",
    "check-size",
    "check-complexity",
]
_CUSTOM_DIR_CHECKERS = [
    "check-bash-logs",
    "check-bash-tests",
]


def _collect(root: Path, suffixes: frozenset[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in suffixes and path.is_file():
            files.append(path)
    return sorted(files)


def _run(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, capture_output=True, text=True)  # noqa: S603
    combined = (result.stdout + result.stderr).strip()
    return result.returncode, combined


def _run_on_files(command: list[str], files: list[Path], findings: list[str]) -> bool:
    if not files:
        return True
    code, output = _run([*command, *[str(f) for f in files]])
    if output:
        findings.extend(output.splitlines())
    return code == 0


def _run_on_dir(command: list[str], root: Path, findings: list[str]) -> bool:
    code, output = _run([*command, str(root)])
    if output:
        findings.extend(output.splitlines())
    return code == 0


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    py_files = _collect(root, frozenset([".py"]))
    sh_files = _collect(root, frozenset([".sh"]))
    all_files = sorted(py_files + sh_files)

    findings: list[str] = []
    passed = True

    for checker in _CUSTOM_FILE_CHECKERS:
        passed &= _run_on_files([checker], all_files, findings)

    for checker in _CUSTOM_DIR_CHECKERS:
        passed &= _run_on_dir([checker], root, findings)

    if py_files:
        passed &= _run_on_files(
            ["ruff", "check", "--line-length", "100",
             "--select", "E,F,I,UP,B,SIM,RET,C,S,N,PLR2004"],
            py_files, findings,
        )
        passed &= _run_on_files(
            ["ruff", "format", "--check", "--line-length", "100"],
            py_files, findings,
        )
        passed &= _run_on_files(
            ["mypy", "--strict", "--python-version", "3.11",
             "--ignore-missing-imports"],
            py_files, findings,
        )
        passed &= _run_on_files(
            ["vulture", "--min-confidence", "80"],
            py_files, findings,
        )
        passed &= _run_on_files(
            ["bandit", "-s", "B101,B404,B603,B607"],
            py_files, findings,
        )
        passed &= _run_on_files(
            ["pylint", "--disable=all", "--enable=C0103"],
            py_files, findings,
        )

    if sh_files and shutil.which("shellcheck"):
        passed &= _run_on_files(["shellcheck"], sh_files, findings)

    for finding in findings:
        print(finding)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
