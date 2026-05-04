from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from install_skill import main as _install_skill_main

_SKIP_DIRS = frozenset(["__pycache__", ".venv", ".git", "node_modules"])
_TEST_DIRS = frozenset(["tests", "test"])
_MIN_DUPLICATE_FILES = 2


def _is_test_file(path: Path) -> bool:
    name = path.name
    return (
        any(part in _TEST_DIRS for part in path.parts)
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


_CUSTOM_FILE_CHECKERS = [
    "check-abbrev",
    "check-comments",
    "check-noqa",
    "check-repeated",
    "check-size",
    "check-complexity",
]
_CUSTOM_DIR_CHECKERS = [
    "check-bash-logs",
    "check-bash-tests",
]


def _collect(root: Path, suffixes: frozenset[str]) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line for line in result.stdout.splitlines() if line]
        return sorted(path for line in lines if (path := root / line).suffix in suffixes and path.is_file())
    except subprocess.CalledProcessError:
        return sorted(
            path
            for path in root.rglob("*")
            if not any(part in _SKIP_DIRS for part in path.parts) and path.suffix in suffixes and path.is_file()
        )


def _user_cache_dir() -> Path:
    return Path(tempfile.gettempdir()) / "dev-quality"


def _handle_install_skill(args: list[str]) -> None:
    sys.argv = ["install-skill"] + args[1:]
    _install_skill_main()
    sys.exit(0)


def _do_clear_cache() -> None:
    cache_dir = _user_cache_dir()
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Cache cleared: {cache_dir}")
    else:
        print(f"No cache found at: {cache_dir}")


def _semgrep_config(root: Path) -> Path | None:
    semgrep_dir = root / ".semgrep"
    if semgrep_dir.is_dir() and (any(semgrep_dir.glob("*.yml")) or any(semgrep_dir.glob("*.yaml"))):
        return semgrep_dir
    for name in ("semgrep.yml", "semgrep.yaml"):
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def _load_config(root: Path) -> dict[str, object]:
    config_file = root / ".dev-quality.yaml"
    if not config_file.exists():
        return {}
    return yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}


def _run(command: list[str], extra_env: dict[str, str] | None = None) -> tuple[int, str]:
    run_env = {**os.environ, **extra_env} if extra_env else None
    result = subprocess.run(command, capture_output=True, text=True, env=run_env)
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
    code, output = _run([*command, *[str(file_path) for file_path in files]], extra_env)
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


def _print_findings(findings: list[str]) -> None:
    for finding in findings:
        print(finding)


def _print_summary(results: dict[str, tuple[bool, int]]) -> None:
    if not results:
        return
    label_width = max(len(k) for k in results) + 2
    separator = "─" * (label_width + 20)
    print()
    print(separator)
    for checker, (ok, count) in results.items():
        if ok:
            status = "PASS"
        else:
            noun = "issue" if count == 1 else "issues"
            status = f"FAIL   {count} {noun}"
        print(f" {checker:<{label_width}} {status}")
    print(separator)
    all_passed = all(ok for ok, _ in results.values())
    total = sum(count for _, count in results.values())
    if all_passed:
        result_status = "PASS"
    else:
        noun = "issue" if total == 1 else "issues"
        result_status = f"FAIL   {total} {noun}"
    print(f" {'Result':<{label_width}} {result_status}")
    print(separator)


def _print_cache_hint(cache_dir: Path) -> None:
    print(f"Cache: {cache_dir}")
    print("  To clear:   check-all --clear-cache")
    print("  To disable: check-all --no-cache .")


def _run_custom_file_checkers(
    all_files: list[Path],
    skip: set[str],
    checker_envs: dict[str, dict[str, str]],
    results: dict[str, tuple[bool, int]],
) -> bool:
    passed = True
    for checker in _CUSTOM_FILE_CHECKERS:
        if checker in skip:
            continue
        findings: list[str] = []
        ok = _run_on_files([checker], all_files, findings, checker_envs.get(checker))
        _print_findings(findings)
        results[checker] = (ok, len(findings))
        passed &= ok
    return passed


def _run_custom_dir_checkers(
    root: Path,
    skip: set[str],
    results: dict[str, tuple[bool, int]],
) -> bool:
    passed = True
    for checker in _CUSTOM_DIR_CHECKERS:
        if checker in skip:
            continue
        findings: list[str] = []
        ok = _run_on_dir([checker], root, findings)
        _print_findings(findings)
        results[checker] = (ok, len(findings))
        passed &= ok
    return passed


def _run_ruff(
    py_files: list[Path],
    skip: set[str],
    ruff_cache: list[str],
    line_length: str,
    results: dict[str, tuple[bool, int]],
) -> bool:
    if "ruff" in skip:
        return True
    passed = True
    findings: list[str] = []
    ok = _run_on_files(
        [
            "ruff",
            "check",
            *ruff_cache,
            "--line-length",
            line_length,
            "--select",
            "E,F,I,UP,B,SIM,RET,C,S,N,PLR2004",
            "--extend-ignore",
            "S101,S603,S607",
            "--per-file-ignores",
            "tests/*.py:PLR2004",
            "--per-file-ignores",
            "test_*.py:PLR2004",
            "--per-file-ignores",
            "*_test.py:PLR2004",
        ],
        py_files,
        findings,
    )
    _print_findings(findings)
    results["ruff check"] = (ok, len(findings))
    passed &= ok
    findings = []
    ok = _run_on_files(
        ["ruff", "format", "--check", *ruff_cache, "--line-length", line_length],
        py_files,
        findings,
    )
    _print_findings(findings)
    results["ruff format"] = (ok, len(findings))
    passed &= ok
    return passed


def _run_py_checkers(
    py_files: list[Path],
    skip: set[str],
    ruff_cache: list[str],
    mypy_cache: list[str],
    line_length: str,
    python_version: str,
    min_duplicate_lines: str,
    results: dict[str, tuple[bool, int]],
) -> bool:
    passed = _run_ruff(py_files, skip, ruff_cache, line_length, results)
    if "mypy" not in skip:
        findings: list[str] = []
        mypy_files = [file_path for file_path in py_files if not _is_test_file(file_path)]
        ok = _run_on_files(
            [
                "mypy",
                "--strict",
                *mypy_cache,
                "--python-version",
                python_version,
                "--ignore-missing-imports",
                "--disable-error-code=import-untyped",
            ],
            mypy_files,
            findings,
        )
        _print_findings(findings)
        results["mypy"] = (ok, len(findings))
        passed &= ok

    if "vulture" not in skip:
        findings = []
        ok = _run_on_files(["vulture", "--min-confidence", "80"], py_files, findings)
        _print_findings(findings)
        results["vulture"] = (ok, len(findings))
        passed &= ok

    if "bandit" not in skip:
        findings = []
        ok = _run_on_files(["bandit", "-s", "B101,B404,B603,B607"], py_files, findings)
        _print_findings(findings)
        results["bandit"] = (ok, len(findings))
        passed &= ok

    if "pylint" not in skip:
        findings = []
        ok = _run_on_files(["pylint", "--disable=all", "--enable=C0103"], py_files, findings)
        _print_findings(findings)
        results["pylint"] = (ok, len(findings))
        passed &= ok

    passed &= _run_check_duplicate(py_files, skip, min_duplicate_lines, results)
    return passed


def _run_check_duplicate(
    py_files: list[Path],
    skip: set[str],
    min_duplicate_lines: str,
    results: dict[str, tuple[bool, int]],
) -> bool:
    if "check-duplicate" in skip:
        return True
    prod_files = [file_path for file_path in py_files if not _is_test_file(file_path)]
    if len(prod_files) < _MIN_DUPLICATE_FILES:
        return True
    findings: list[str] = []
    ok = _run_on_files(
        ["pylint", "--disable=all", "--enable=R0801", f"--min-similarity-lines={min_duplicate_lines}"],
        prod_files,
        findings,
    )
    _print_findings(findings)
    results["check-duplicate"] = (ok, len(findings))
    return ok


def _run_sh_checkers(
    sh_files: list[Path],
    skip: set[str],
    results: dict[str, tuple[bool, int]],
) -> bool:
    if sh_files and "shellcheck" not in skip:
        findings: list[str] = []
        ok = _run_on_files(["shellcheck"], sh_files, findings)
        _print_findings(findings)
        results["shellcheck"] = (ok, len(findings))
        return ok
    return True


def _run_semgrep(
    root: Path,
    skip: set[str],
    results: dict[str, tuple[bool, int]],
) -> bool:
    semgrep_conf = _semgrep_config(root)
    if semgrep_conf and "semgrep" not in skip and shutil.which("semgrep"):
        findings: list[str] = []
        ok = _run_on_dir(["semgrep", "--config", str(semgrep_conf), "--error"], root, findings)
        _print_findings(findings)
        results["semgrep"] = (ok, len(findings))
        return ok
    return True


def _build_size_env(config: dict[str, object]) -> dict[str, str]:
    return {
        "CHECK_SIZE_MAX_FILE": str(config.get("max_file_lines", 800)),
        "CHECK_SIZE_MAX_FUNC": str(config.get("max_func_lines", 100)),
        "CHECK_SIZE_MAX_TEST_FILE": str(config.get("max_test_file_lines", 1500)),
    }


def _build_abbrev_env(config: dict[str, object]) -> dict[str, str]:
    min_length = str(config.get("abbrev_min_length", 2))
    extra = list(config.get("abbrev_allowlist", []))  # type: ignore[call-overload]
    abbrev_env: dict[str, str] = {"CHECK_ABBREV_MIN_LENGTH": min_length}
    if extra:
        abbrev_env["CHECK_ABBREV_ALLOWLIST_EXTRA"] = ",".join(str(item) for item in extra)
    return abbrev_env


def _build_repeated_env(config: dict[str, object]) -> dict[str, str]:
    return {
        "CHECK_REPEATED_MAX_REPETITIONS": str(config.get("max_line_repetitions", 2)),
        "CHECK_REPEATED_MIN_LINE_LENGTH": str(config.get("min_line_length", 20)),
    }


def _print_footer(outdated_warning: str | None, cache_dir: Path | None) -> None:
    if outdated_warning:
        print(outdated_warning, flush=True)
    if cache_dir is not None:
        _print_cache_hint(cache_dir)


def _warn_if_precommit_outdated(root: Path) -> str | None:
    config_path = root / ".pre-commit-config.yaml"
    if not config_path.exists():
        return None
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        for repo in data.get("repos", []):
            if "lipex360x/dev-quality" not in str(repo.get("repo", "")):
                continue
            pinned = str(repo.get("rev", ""))
            current = f"v{importlib.metadata.version('dev-quality')}"
            if pinned != current:
                message = (
                    f"WARNING: .pre-commit-config.yaml is pinned to {pinned} "
                    f"but this tool is at {current}. "
                    f"Run `pre-commit autoupdate` to sync."
                )
                print(message, flush=True)
                return message
    except (OSError, yaml.YAMLError, importlib.metadata.PackageNotFoundError):
        return None
    return None


def main() -> None:
    clear_cache = "--clear-cache" in sys.argv
    no_cache = "--no-cache" in sys.argv
    args = [flag for flag in sys.argv[1:] if flag not in {"--no-cache", "--clear-cache"}]

    if clear_cache:
        _do_clear_cache()
        sys.exit(0)

    if args and args[0] == "install-skill":
        _handle_install_skill(args)

    root = Path(args[0]).resolve() if args else Path.cwd()
    print(f"Scanning {root} ...", flush=True)
    outdated_warning = _warn_if_precommit_outdated(root)

    config = _load_config(root)
    skip = set(config.get("skip", []))  # type: ignore[call-overload]
    line_length = str(config.get("line_length", 120))
    max_complexity = str(config.get("max_complexity", 6))
    python_version = str(config.get("python_version", "3.11"))
    min_duplicate_lines = str(config.get("min_duplicate_lines", 6))

    if no_cache:
        ruff_cache: list[str] = ["--no-cache"]
        mypy_cache: list[str] = ["--no-incremental"]
        cache_dir = None
    else:
        cache_dir = _user_cache_dir()
        ruff_cache = ["--cache-dir", str(cache_dir / "ruff")]
        mypy_cache = ["--cache-dir", str(cache_dir / "mypy")]

    py_files = _collect(root, frozenset([".py"]))
    sh_files = _collect(root, frozenset([".sh"]))
    all_files = sorted(py_files + sh_files)

    results: dict[str, tuple[bool, int]] = {}
    size_env = _build_size_env(config)
    complexity_env = {"CHECK_COMPLEXITY_MAX": max_complexity}
    abbrev_env = _build_abbrev_env(config)
    repeated_env = _build_repeated_env(config)
    checker_envs: dict[str, dict[str, str]] = {
        "check-size": size_env,
        "check-complexity": complexity_env,
        "check-abbrev": abbrev_env,
        "check-repeated": repeated_env,
    }

    passed = _run_custom_file_checkers(all_files, skip, checker_envs, results)
    passed &= _run_custom_dir_checkers(root, skip, results)
    if py_files:
        passed &= _run_py_checkers(
            py_files, skip, ruff_cache, mypy_cache, line_length, python_version, min_duplicate_lines, results
        )
    passed &= _run_sh_checkers(sh_files, skip, results)
    passed &= _run_semgrep(root, skip, results)

    _print_summary(results)
    _print_footer(outdated_warning, cache_dir)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
