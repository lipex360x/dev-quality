from __future__ import annotations

import sys
from importlib.resources import files
from pathlib import Path


def _config_file() -> Path:
    return Path.home() / ".config" / "dev-quality" / "skill_path"


def _save_skill_path(path: Path, config_file: Path) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(str(path), encoding="utf-8")


def _load_skill_path(config_file: Path) -> Path | None:
    if not config_file.exists():
        return None
    return Path(config_file.read_text(encoding="utf-8").strip())


def _resolve_target(config_file: Path) -> Path:
    argv = sys.argv[1:]
    if "--target" in argv:
        position = argv.index("--target")
        if position + 1 < len(argv):
            return Path(argv[position + 1])
        print("Usage: install-skill --target <skills-directory>")
        sys.exit(1)
    saved = _load_skill_path(config_file)
    if saved is not None:
        return saved
    print("Usage: install-skill --target <skills-directory>")
    print("Example: install-skill --target ~/.claude/skills")
    print("Tip: once installed, run without --target to update in-place.")
    sys.exit(1)


def _copy_skill_files(destination_dir: Path) -> list[Path]:
    package = files("dev_quality_skill")
    destination_dir.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    for resource in sorted(package.iterdir(), key=lambda resource: resource.name):
        if resource.name.endswith(".md"):
            destination = destination_dir / resource.name
            destination.write_text(resource.read_text(encoding="utf-8"), encoding="utf-8")
            installed.append(destination)
    return installed


def main(config_file: Path | None = None) -> None:
    if config_file is None:
        config_file = _config_file()
    target = _resolve_target(config_file).expanduser()
    destination_dir = target / "dev-quality"
    installed = _copy_skill_files(destination_dir)
    _save_skill_path(target, config_file)
    print(f"Skill installed at {destination_dir}")
    for path in installed:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
