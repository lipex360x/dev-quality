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


def main(config_file: Path | None = None) -> None:
    if config_file is None:
        config_file = _config_file()
    target = _resolve_target(config_file).expanduser()
    destination_dir = target / "dev-quality"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / "SKILL.md"
    skill_text = files("dev_quality_skill").joinpath("SKILL.md").read_text(encoding="utf-8")
    destination.write_text(skill_text, encoding="utf-8")
    _save_skill_path(target, config_file)
    print(f"Skill installed at {destination}")


if __name__ == "__main__":
    main()
