from __future__ import annotations

import sys
from importlib.resources import files
from pathlib import Path


def _parse_target() -> str:
    argv = sys.argv[1:]
    if "--target" in argv:
        position = argv.index("--target")
        if position + 1 < len(argv):
            return argv[position + 1]
    return str(Path.home() / ".claude" / "skills")


def main() -> None:
    target_dir = Path(_parse_target()).expanduser() / "dev-quality"
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / "SKILL.md"
    skill_text = files("dev_quality_skill").joinpath("SKILL.md").read_text(encoding="utf-8")
    destination.write_text(skill_text, encoding="utf-8")
    print(f"Skill installed at {destination}")


if __name__ == "__main__":
    main()
