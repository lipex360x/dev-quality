from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

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


def _load_config(root: Path) -> dict[str, object]:
    config_file = root / ".dev-quality.yaml"
    if not config_file.exists():
        return {}
    return yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}


def _run(
    command: list[str], extra_env: dict[str, str] | None = None
) -> tuple[int, str]:
    env = {**os.environ, **extra_env} if extra_env else None
    result = subprocess.run(command, capture_output=True, text=True, env=env)  # noqa: S603
    combined = (result.stdout + result.stderr).strip()
    return result.returncode, combined


def _run_on_files(
    command: list[str],
    files: list[Path],
    findings: list[str],
    extra_env: dict[str, str] | None = None,
) -> bool:
    if not files:
        return True
    code, output = _run([*command, *[str(f) for f in files]], extra_env)
    if output:
        findings.extend(output.splitlines())
    return code == 0


def _run_on_dir(
    command: list[str],
    root: Path,
    findings: list[str],
    extra_env: dict[str, str] | None = None,
) -> bool:
    code, output = _run([*command, str(root)], extra_env)
    if output:
        findings.extend(output.splitlines())
    return code == 0


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    config = _load_config(root)

    skip = set(config.get("skip", []))  # type: ignore[arg-type]
    line_length = str(config.get("line_length", 100))
    max_complexity = str(config.get("max_complexity", 6))
    max_file_lines = str(config.get("max_file_lines", 800))
    max_func_lines = str(config.get("max_func_lines", 80))
    python_version = str(config.get("python_version", "3.11"))

    py_files = _collect(root, frozenset([".py"]))
    sh_files = _collect(root, frozenset([".sh"]))
    all_files = sorted(py_files + sh_files)

    findings: list[str] = []
    passed = True

    size_env = {"CHECK_SIZE_MAX_FILE": max_file_lines, "CHECK_SIZE_MAX_FUNC": max_func_lines}
    complexity_env = {"CHECK_COMPLEXITY_MAX": max_complexity}

    for checker in _CUSTOM_FILE_CHECKERS:
        if checker in skip:
            continue
        extra_env: dict[str, str] | None = None
        if checker == "check-size":
            extra_env = size_env
        elif checker == "check-complexity":
            extra_env = complexity_env
        passed &= _run_on_files([checker], all_files, findings, extra_env)

    for checker in _CUSTOM_DIR_CHECKERS:
        if checker in skip:
            continue
        passed &= _run_on_dir([checker], root, findings)

    if py_files:
        if "ruff" not in skip:
            passed &= _run_on_files(
                ["ruff", "check", "--line-length", line_length,
                 "--select", "E,F,I,UP,B,SIM,RET,C,S,N,PLR2004"],
                py_files, findings,
            )
            passed &= _run_on_files(
                ["ruff", "format", "--check", "--line-length", line_length],
                py_files, findings,
            )
        if "mypy" not in skip:
            passed &= _run_on_files(
                ["mypy", "--strict", "--python-version", python_version,
                 "--ignore-missing-imports"],
                py_files, findings,
            )
        if "vulture" not in skip:
            passed &= _run_on_files(["vulture", "--min-confidence", "80"], py_files, findings)
        if "bandit" not in skip:
            passed &= _run_on_files(["bandit", "-s", "B101,B404,B603,B607"], py_files, findings)
        if "pylint" not in skip:
            passed &= _run_on_files(
                ["pylint", "--disable=all", "--enable=C0103"], py_files, findings
            )

    if sh_files and "shellcheck" not in skip:
        passed &= _run_on_files(["shellcheck"], sh_files, findings)

    for finding in findings:
        print(finding)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
