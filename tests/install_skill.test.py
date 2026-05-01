from __future__ import annotations

import sys
from pathlib import Path

import pytest
from install_skill import _parse_target, main


def test_parse_target_returns_explicit_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", "/my/skills"])
    assert _parse_target() == "/my/skills"


def test_parse_target_defaults_to_claude_skills(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill"])
    assert ".claude/skills" in _parse_target()


def test_parse_target_defaults_when_target_flag_has_no_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target"])
    assert ".claude/skills" in _parse_target()


def test_install_creates_skill_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main()
    assert (tmp_path / "dev-quality").is_dir()


def test_install_writes_skill_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main()
    destination = tmp_path / "dev-quality" / "SKILL.md"
    assert destination.exists()
    assert len(destination.read_text(encoding="utf-8")) > 100


def test_install_skill_md_contains_dev_quality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main()
    content = (tmp_path / "dev-quality" / "SKILL.md").read_text(encoding="utf-8")
    assert "dev-quality" in content


def test_install_prints_destinationination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main()
    out = capsys.readouterr().out
    assert "SKILL.md" in out


def test_install_overwrites_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination_dir = tmp_path / "dev-quality"
    destination_dir.mkdir()
    (destination_dir / "SKILL.md").write_text("old content", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["install-skill", "--target", str(tmp_path)])
    main()
    content = (destination_dir / "SKILL.md").read_text(encoding="utf-8")
    assert content != "old content"
