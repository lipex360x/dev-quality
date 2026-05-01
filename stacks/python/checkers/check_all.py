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
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line for line in result.stdout.splitlines() if line]
        return sorted(root / line for line in lines if Path(line).suffix in suffixes)
    except subprocess.CalledProcessError:
        return sorted(
            path
            for path in root.rglob("*")
            if not any(part in _SKIP_DIRS for part in path.parts)
            and path.suffix in suffixes
            and path.is_file()
        )


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


def _print_summary(results: dict[str, tuple[bool, int]]) -> None:
    if not results:
        return
    label_width = max(len(k) for k in results) + 2
    sep = "─" * (label_width + 20)
    print()
    print(sep)
    for checker, (ok, count) in results.items():
        if ok:
            status = "PASS"
        else:
            noun = "issue" if count == 1 else "issues"
            status = f"FAIL   {count} {noun}"
        print(f" {checker:<{label_width}} {status}")
    print(sep)
    all_passed = all(ok for ok, _ in results.values())
    total = sum(count for _, count in results.values())
    if all_passed:
        result_status = "PASS"
    else:
        noun = "issue" if total == 1 else "issues"
        result_status = f"FAIL   {total} {noun}"
    print(f" {'Result':<{label_width}} {result_status}")
    print(sep)


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
    results: dict[str, tuple[bool, int]] = {}
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
        start = len(findings)
        ok = _run_on_files([checker], all_files, findings, extra_env)
        results[checker] = (ok, len(findings) - start)
        passed &= ok

    for checker in _CUSTOM_DIR_CHECKERS:
        if checker in skip:
            continue
        start = len(findings)
        ok = _run_on_dir([checker], root, findings)
        results[checker] = (ok, len(findings) - start)
        passed &= ok

    if py_files:
        if "ruff" not in skip:
            start = len(findings)
            ok = _run_on_files(
                [
                    "ruff", "check",
                    "--no-cache",
                    "--line-length", line_length,
                    "--select", "E,F,I,UP,B,SIM,RET,C,S,N,PLR2004",
                    "--extend-ignore", "S101",
                ],
                py_files, findings,
            )
            results["ruff check"] = (ok, len(findings) - start)
            passed &= ok

            start = len(findings)
            ok = _run_on_files(
                ["ruff", "format", "--check", "--no-cache", "--line-length", line_length],
                py_files, findings,
            )
            results["ruff format"] = (ok, len(findings) - start)
            passed &= ok

        if "mypy" not in skip:
            start = len(findings)
            ok = _run_on_files(
                ["mypy", "--strict", "--no-incremental",
                 "--python-version", python_version, "--ignore-missing-imports"],
                py_files, findings,
            )
            results["mypy"] = (ok, len(findings) - start)
            passed &= ok

        if "vulture" not in skip:
            start = len(findings)
            ok = _run_on_files(["vulture", "--min-confidence", "80"], py_files, findings)
            results["vulture"] = (ok, len(findings) - start)
            passed &= ok

        if "bandit" not in skip:
            start = len(findings)
            ok = _run_on_files(["bandit", "-s", "B101,B404,B603,B607"], py_files, findings)
            results["bandit"] = (ok, len(findings) - start)
            passed &= ok

        if "pylint" not in skip:
            start = len(findings)
            ok = _run_on_files(
                ["pylint", "--disable=all", "--enable=C0103"], py_files, findings
            )
            results["pylint"] = (ok, len(findings) - start)
            passed &= ok

    if sh_files and "shellcheck" not in skip:
        start = len(findings)
        ok = _run_on_files(["shellcheck"], sh_files, findings)
        results["shellcheck"] = (ok, len(findings) - start)
        passed &= ok

    for finding in findings:
        print(finding)

    _print_summary(results)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
