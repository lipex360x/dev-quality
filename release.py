from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path


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
        ["git", "tag", "--list", f"v{version}"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def _create_release(tag: str, notes: str) -> None:
    subprocess.run(["git", "tag", tag], check=True)  # noqa: S603
    subprocess.run(["git", "push", "origin", tag], check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        ["gh", "release", "create", tag, "--title", tag, "--notes", notes],
        check=True,
    )
    print(f"Released {tag}")


def main(root: Path | None = None) -> None:
    dry_run = "--dry-run" in sys.argv
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
