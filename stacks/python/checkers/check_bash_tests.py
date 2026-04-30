from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_EXEMPT_DIRS = {"hooks", "tests"}


def _find_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()


def _script_is_covered(script: Path, scripts_dir: Path, tests_dir: Path) -> bool:
    parts = script.relative_to(scripts_dir).parts
    if any(part in _EXEMPT_DIRS for part in parts):
        return True
    return (tests_dir / f"{script.stem}.test.sh").exists()


def check_bash_tests(root: Path) -> list[str] | None:
    scripts_dir = root / "scripts" / "bash"
    if not scripts_dir.exists():
        return None

    tests_dir = scripts_dir / "tests"
    findings: list[str] = []

    for script in sorted(scripts_dir.rglob("*.sh")):
        if not _script_is_covered(script, scripts_dir, tests_dir):
            findings.append(f"MISSING_TEST:{script.relative_to(root)}")

    if not findings:
        findings.append("PASS:bash-tests")

    return findings


def main() -> None:
    args = sys.argv[1:]
    root = Path(args[0]).resolve() if args else _find_root()

    result = check_bash_tests(root)
    if result is None:
        sys.exit(0)

    for finding in result:
        print(finding)

    has_failures = any(finding.startswith(("MISSING_TEST:", "FAIL:")) for finding in result)
    sys.exit(1 if has_failures else 0)


if __name__ == "__main__":
    main()
