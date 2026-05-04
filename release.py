from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path


def _check_gh_auth() -> None:
    if not shutil.which("gh"):
        print("Error: gh CLI not found — install it from https://cli.github.com")
        sys.exit(1)
    result = subprocess.run(["gh", "auth", "status"], capture_output=True)  # noqa: S603, S607
    if result.returncode != 0:
        print("Error: gh CLI not authenticated — run: gh auth login")
        sys.exit(1)


def _read_version_from_changelog(root: Path) -> str:
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"## \[v([\d.]+)\]", text)
    if not match:
        print("Error: no version found in CHANGELOG.md")
        sys.exit(1)
    return match.group(1)


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


def _update_pyproject_version(root: Path, version: str) -> bool:
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    updated = re.sub(
        r'^(version\s*=\s*")[^"]+(")',
        rf"\g<1>{version}\2",
        text,
        flags=re.MULTILINE,
    )
    if updated == text:
        return False
    pyproject.write_text(updated, encoding="utf-8")
    return True


def _update_readme_version(root: Path, version: str) -> bool:
    readme = root / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    updated = re.sub(
        r"(https://img\.shields\.io/badge/version-)v[\d.]+(-blue)",
        rf"\g<1>v{version}\2",
        text,
    )
    updated = re.sub(r"(rev:\s*)v[\d.]+", rf"\g<1>v{version}", updated)
    if updated == text:
        return False
    readme.write_text(updated, encoding="utf-8")
    return True


def _commit_version_bump(root: Path, version: str) -> None:
    subprocess.run(  # noqa: S603, S607
        ["git", "add", "pyproject.toml", "README.md"], cwd=str(root), check=True
    )
    subprocess.run(  # noqa: S603
        ["git", "commit", "-m", f"chore: bump version to v{version}"],  # noqa: S607
        cwd=str(root),
        check=True,
    )
    subprocess.run(["git", "push"], cwd=str(root), check=True)  # noqa: S603, S607


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


def _preflight_release(version: str, tag: str) -> None:
    _check_gh_auth()
    if _tag_exists(version):
        print(f"Error: tag {tag} already exists")
        sys.exit(1)


def main(root: Path | None = None) -> None:
    dry_run = "--dry-run" in sys.argv
    release = "--release" in sys.argv
    if root is None:
        root = Path(__file__).parent
    version = _read_version_from_changelog(root)
    tag = f"v{version}"

    if release:
        _preflight_release(version, tag)

    notes = _extract_changelog_entry(root, version)

    if dry_run:
        print(f"Version:  {version}")
        print(f"Tag:      {tag}")
        print(f"Notes:\n{notes}")
        return

    pyproject_changed = _update_pyproject_version(root, version)
    readme_changed = _update_readme_version(root, version)

    if pyproject_changed or readme_changed:
        _commit_version_bump(root, version)

    if release:
        _create_release(tag, notes)


if __name__ == "__main__":
    main()
