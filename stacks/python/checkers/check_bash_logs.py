from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_EXEMPT_DIRS = {"hooks", "tests", "lib"}
_EXEMPT_SCRIPTS = {"statusline.sh"}


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


def _script_needs_log(script: Path, scripts_dir: Path) -> bool:
    parts = script.relative_to(scripts_dir).parts
    if any(part in _EXEMPT_DIRS for part in parts):
        return False
    return script.name not in _EXEMPT_SCRIPTS


def _has_log_init(script: Path) -> bool:
    return "log::init_script" in script.read_text(encoding="utf-8")


def check_bash_logs(root: Path) -> list[str] | None:
    scripts_dir = root / "scripts" / "bash"
    if not scripts_dir.exists():
        return None

    findings: list[str] = []

    for script in sorted(scripts_dir.rglob("*.sh")):
        if not _script_needs_log(script, scripts_dir):
            continue
        if not _has_log_init(script):
            findings.append(f"MISSING_LOG:{script.relative_to(root)}")

    if not findings:
        findings.append("PASS:bash-logs")

    return findings


def main() -> None:
    args = sys.argv[1:]
    root = Path(args[0]).resolve() if args else _find_root()

    result = check_bash_logs(root)
    if result is None:
        sys.exit(0)

    for finding in result:
        print(finding)

    has_failures = any(finding.startswith(("MISSING_LOG:", "FAIL:")) for finding in result)
    sys.exit(1 if has_failures else 0)


if __name__ == "__main__":
    main()
