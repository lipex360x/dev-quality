from __future__ import annotations

import sys
from pathlib import Path

import pytest
from install_skill import (
    _config_file,
    _copy_skill_files,
    _load_skill_path,
    _resolve_target,
    _save_skill_path,
    main,
)


def test_config_file_returns_path_under_home() -> None:
    result = _config_file()
    assert result == Path.home() / ".config" / "dev-quality" / "skill_path"


def test_save_skill_path_writes_file(tmp_path: Path) -> None:
    config = tmp_path / "skill_path"
    _save_skill_path(Path("/my/skills"), config)
    assert config.read_text(encoding="utf-8") == "/my/skills"


def test_save_skill_path_creates_parent_directories(tmp_path: Path) -> None:
    config = tmp_path / "nested" / "dirs" / "skill_path"
    _save_skill_path(Path("/my/skills"), config)
    assert config.exists()


def test_load_skill_path_returns_none_when_no_file(tmp_path: Path) -> None:
    config = tmp_path / "skill_path"
    assert _load_skill_path(config) is None


def test_load_skill_path_returns_saved_path(tmp_path: Path) -> None:
    config = tmp_path / "skill_path"
    config.write_text("/my/skills", encoding="utf-8")
    assert _load_skill_path(config) == Path("/my/skills")


def test_load_skill_path_strips_whitespace(tmp_path: Path) -> None:
    config = tmp_path / "skill_path"
    config.write_text("/my/skills\n", encoding="utf-8")
    assert _load_skill_path(config) == Path("/my/skills")


def test_resolve_target_uses_explicit_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", "/explicit/path"])
    config = tmp_path / "skill_path"
    assert _resolve_target(config) == Path("/explicit/path")


def test_resolve_target_falls_back_to_saved_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    config = tmp_path / "skill_path"
    config.write_text(str(tmp_path / "skills"), encoding="utf-8")
    assert _resolve_target(config) == tmp_path / "skills"


def test_resolve_target_exits_when_no_target_and_no_saved_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    config = tmp_path / "skill_path"
    with pytest.raises(SystemExit) as raised:
        _resolve_target(config)
    assert raised.value.code == 1


def test_resolve_target_prints_usage_when_no_target_and_no_saved_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    config = tmp_path / "skill_path"
    with pytest.raises(SystemExit):
        _resolve_target(config)
    assert "--target" in capsys.readouterr().out


def test_resolve_target_exits_when_target_flag_has_no_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target"])
    config = tmp_path / "skill_path"
    with pytest.raises(SystemExit) as raised:
        _resolve_target(config)
    assert raised.value.code == 1


def test_copy_skill_files_creates_skill_md(tmp_path: Path) -> None:
    _copy_skill_files(tmp_path)
    assert (tmp_path / "SKILL.md").exists()


def test_copy_skill_files_creates_python_md(tmp_path: Path) -> None:
    _copy_skill_files(tmp_path)
    assert (tmp_path / "python.md").exists()


def test_copy_skill_files_creates_bash_md(tmp_path: Path) -> None:
    _copy_skill_files(tmp_path)
    assert (tmp_path / "bash.md").exists()


def test_copy_skill_files_creates_parent_directory(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "dir"
    _copy_skill_files(destination)
    assert destination.is_dir()


def test_copy_skill_files_returns_sorted_paths(tmp_path: Path) -> None:
    result = _copy_skill_files(tmp_path)
    names = [path.name for path in result]
    assert names == sorted(names)


def test_copy_skill_files_returns_only_md_files(tmp_path: Path) -> None:
    result = _copy_skill_files(tmp_path)
    assert all(path.suffix == ".md" for path in result)


def test_install_creates_skill_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    assert (tmp_path / "dev-quality").is_dir()


def test_install_copies_all_md_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    destination = tmp_path / "dev-quality"
    assert (destination / "SKILL.md").exists()
    assert (destination / "python.md").exists()
    assert (destination / "bash.md").exists()


def test_install_skill_md_contains_dev_quality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    content = (tmp_path / "dev-quality" / "SKILL.md").read_text(encoding="utf-8")
    assert "dev-quality" in content


def test_install_prints_destination_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    out = capsys.readouterr().out
    assert str(tmp_path / "dev-quality") in out


def test_install_prints_each_installed_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    out = capsys.readouterr().out
    assert "SKILL.md" in out
    assert "python.md" in out
    assert "bash.md" in out


def test_install_overwrites_existing_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "skill_path"
    destination_dir = tmp_path / "dev-quality"
    destination_dir.mkdir()
    (destination_dir / "SKILL.md").write_text("old content", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    content = (destination_dir / "SKILL.md").read_text(encoding="utf-8")
    assert content != "old content"


def test_install_saves_target_path_to_config_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "skill_path"
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main(config_file=config)
    assert config.exists()
    assert str(tmp_path) in config.read_text(encoding="utf-8")


def test_install_updates_without_target_when_path_is_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "skill_path"
    skills_dir = tmp_path / "skills"
    config.write_text(str(skills_dir), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    main(config_file=config)
    assert (skills_dir / "dev-quality" / "SKILL.md").exists()
    assert (skills_dir / "dev-quality" / "python.md").exists()
    assert (skills_dir / "dev-quality" / "bash.md").exists()


def test_install_prints_updated_path_on_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "skill_path"
    skills_dir = tmp_path / "skills"
    config.write_text(str(skills_dir), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    main(config_file=config)
    out = capsys.readouterr().out
    assert "SKILL.md" in out
