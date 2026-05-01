from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def _check_gh_auth() -> None:
    if not shutil.which("gh"):
        print("Error: gh CLI not found — install it from https://cli.github.com")
        sys.exit(1)
    result = subprocess.run(["gh", "auth", "status"], capture_output=True)  # noqa: S603, S607
    if result.returncode != 0:
        print("Error: gh CLI not authenticated — run: gh auth login")
        sys.exit(1)


def _read_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _extract_changelog_entry(root: Path, version: str) -> str:
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"## \[v{re.escape(version)}\][^\n]*\n(.*?)(?=\n## \[|$)",
        text,
        re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


def _tag_exists(version: str) -> bool:
    result = subprocess.run(  # noqa: S603
        ["git", "tag", "--list", f"v{version}"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def _create_release(tag: str, notes: str) -> None:
    subprocess.run(["git", "tag", tag], check=True)  # noqa: S603, S607
    subprocess.run(["git", "push", "origin", tag], check=True)  # noqa: S603, S607
    subprocess.run(  # noqa: S603
        ["gh", "release", "create", tag, "--title", tag, "--notes", notes],  # noqa: S607
        check=True,
    )
    print(f"Released {tag}")


def main(root: Path | None = None) -> None:
    dry_run = "--dry-run" in sys.argv
    _check_gh_auth()
    if root is None:
        root = Path(__file__).parent
    version = _read_version(root)
    tag = f"v{version}"

    if _tag_exists(version):
        print(f"Error: tag {tag} already exists")
        sys.exit(1)

    notes = _extract_changelog_entry(root, version)

    if dry_run:
        print(f"Version:  {version}")
        print(f"Tag:      {tag}")
        print(f"Notes:\n{notes}")
        return

    _create_release(tag, notes)


if __name__ == "__main__":
    main()
