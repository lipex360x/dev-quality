from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from release import (
    _check_gh_auth,
    _commit_version_bump,
    _create_release,
    _extract_changelog_entry,
    _preflight_release,
    _read_version_from_changelog,
    _tag_exists,
    _update_pyproject_version,
    _update_readme_version,
    main,
)

_PYPROJECT_CURRENT = """\
[project]
name = "dev-quality"
version = "1.2.3"
"""

_PYPROJECT_OUTDATED = """\
[project]
name = "dev-quality"
version = "1.2.2"
"""

_CHANGELOG = """\
# Changelog

---

## [v1.2.3] — 2026-01-01

### Added
- new feature

---

## [v1.2.2] — 2025-12-01

### Fixed
- bug fix
"""

_README_WITH_OLD_BADGE = (
    "[![Version](https://img.shields.io/badge/version-v0.5.0-blue)]"
    "(https://github.com/lipex360x/dev-quality/releases)\n"
)
_README_WITH_CURRENT_BADGE = (
    "[![Version](https://img.shields.io/badge/version-v1.2.3-blue)]"
    "(https://github.com/lipex360x/dev-quality/releases)\n"
)
_README_WITHOUT_BADGE = "# dev-quality\n\nNo badge here.\n"
_README_WITH_REV_EXAMPLES = (
    "[![Version](https://img.shields.io/badge/version-v0.5.0-blue)]"
    "(https://github.com/lipex360x/dev-quality/releases)\n\n"
    "```yaml\nrepos:\n  - repo: https://github.com/lipex360x/dev-quality\n"
    "    rev: v0.5.0\n    hooks:\n      - id: check-all\n```\n\n"
    "```yaml\nrepos:\n  - repo: https://github.com/lipex360x/dev-quality\n"
    "    rev: v0.4.0\n    hooks:\n      - id: check-abbrev\n```\n"
)


def test_read_version_from_changelog_returns_top_version(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    assert _read_version_from_changelog(tmp_path) == "1.2.3"


def test_read_version_from_changelog_ignores_older_versions(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    assert _read_version_from_changelog(tmp_path) != "1.2.2"


def test_read_version_from_changelog_exits_when_no_version_found(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\nNo versions here.\n", encoding="utf-8")
    with pytest.raises(SystemExit) as raised:
        _read_version_from_changelog(tmp_path)
    assert raised.value.code == 1


def test_extract_changelog_entry_returns_content(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    entry = _extract_changelog_entry(tmp_path, "1.2.3")
    assert "new feature" in entry


def test_extract_changelog_entry_does_not_bleed_into_next_version(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    entry = _extract_changelog_entry(tmp_path, "1.2.3")
    assert "bug fix" not in entry


def test_extract_changelog_entry_returns_empty_when_version_absent(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    assert _extract_changelog_entry(tmp_path, "9.9.9") == ""


def test_update_pyproject_version_rewrites_version(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    _update_pyproject_version(tmp_path, "1.2.3")
    assert 'version = "1.2.3"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")


def test_update_pyproject_version_removes_old_version(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    _update_pyproject_version(tmp_path, "1.2.3")
    assert 'version = "1.2.2"' not in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")


def test_update_pyproject_version_returns_true_when_changed(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    assert _update_pyproject_version(tmp_path, "1.2.3") is True


def test_update_pyproject_version_returns_false_when_already_current(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    assert _update_pyproject_version(tmp_path, "1.2.3") is False


def test_update_readme_version_rewrites_badge(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITH_OLD_BADGE, encoding="utf-8")
    _update_readme_version(tmp_path, "1.2.3")
    assert "v1.2.3" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_update_readme_version_removes_old_version(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITH_OLD_BADGE, encoding="utf-8")
    _update_readme_version(tmp_path, "1.2.3")
    assert "v0.5.0" not in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_update_readme_version_returns_true_when_changed(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITH_OLD_BADGE, encoding="utf-8")
    assert _update_readme_version(tmp_path, "1.2.3") is True


def test_update_readme_version_returns_false_when_badge_absent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITHOUT_BADGE, encoding="utf-8")
    assert _update_readme_version(tmp_path, "1.2.3") is False


def test_update_readme_version_returns_false_when_readme_absent(tmp_path: Path) -> None:
    assert _update_readme_version(tmp_path, "1.2.3") is False


def test_update_readme_version_no_op_when_badge_absent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITHOUT_BADGE, encoding="utf-8")
    _update_readme_version(tmp_path, "1.2.3")
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == _README_WITHOUT_BADGE


def test_update_readme_version_rewrites_rev_examples(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITH_REV_EXAMPLES, encoding="utf-8")
    _update_readme_version(tmp_path, "1.2.3")
    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert content.count("rev: v1.2.3") == 2


def test_update_readme_version_removes_old_rev_versions(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(_README_WITH_REV_EXAMPLES, encoding="utf-8")
    _update_readme_version(tmp_path, "1.2.3")
    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "rev: v0.5.0" not in content
    assert "rev: v0.4.0" not in content


def test_update_readme_version_returns_true_when_only_rev_changed(tmp_path: Path) -> None:
    readme_only_rev = (
        "# dev-quality\n\n"
        "```yaml\nrepos:\n  - repo: https://github.com/lipex360x/dev-quality\n"
        "    rev: v0.5.0\n```\n"
    )
    (tmp_path / "README.md").write_text(readme_only_rev, encoding="utf-8")
    assert _update_readme_version(tmp_path, "1.2.3") is True


def test_commit_version_bump_stages_pyproject_and_readme(tmp_path: Path) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _commit_version_bump(tmp_path, "1.2.3")
    add_call = next(
        invocation[0][0]
        for invocation in mock_run.call_args_list
        if invocation[0][0][:2] == ["git", "add"]
    )
    assert "pyproject.toml" in add_call
    assert "README.md" in add_call


def test_commit_version_bump_commits(tmp_path: Path) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _commit_version_bump(tmp_path, "1.2.3")
    commands = [invocation[0][0] for invocation in mock_run.call_args_list]
    assert any(command[:2] == ["git", "commit"] for command in commands)


def test_commit_version_bump_pushes(tmp_path: Path) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _commit_version_bump(tmp_path, "1.2.3")
    commands = [invocation[0][0] for invocation in mock_run.call_args_list]
    assert any(command[:2] == ["git", "push"] for command in commands)


def test_commit_version_bump_message_contains_version(tmp_path: Path) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _commit_version_bump(tmp_path, "1.2.3")
    commit_call = next(
        invocation[0][0]
        for invocation in mock_run.call_args_list
        if invocation[0][0][:2] == ["git", "commit"]
    )
    assert any("1.2.3" in part for part in commit_call)


def test_preflight_release_calls_gh_auth() -> None:
    with (
        patch("release._check_gh_auth") as mock_auth,
        patch("release._tag_exists", return_value=False),
    ):
        _preflight_release("1.2.3", "v1.2.3")
    mock_auth.assert_called_once()


def test_preflight_release_aborts_when_tag_exists() -> None:
    with (
        patch("release._check_gh_auth"),
        patch("release._tag_exists", return_value=True),
        pytest.raises(SystemExit) as raised,
    ):
        _preflight_release("1.2.3", "v1.2.3")
    assert raised.value.code == 1


def test_preflight_release_passes_when_tag_absent() -> None:
    with (
        patch("release._check_gh_auth"),
        patch("release._tag_exists", return_value=False),
    ):
        _preflight_release("1.2.3", "v1.2.3")


def test_tag_exists_returns_false_when_absent() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        assert _tag_exists("9.9.9") is False


def test_tag_exists_returns_true_when_present() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="v9.9.9\n")
        assert _tag_exists("9.9.9") is True


def test_tag_exists_passes_version_to_git() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        _tag_exists("1.2.3")
    args = mock_run.call_args[0][0]
    assert "v1.2.3" in args


def test_create_release_calls_git_tag() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _create_release("v1.0.0", "notes")
    commands = [invocation[0][0] for invocation in mock_run.call_args_list]
    assert any(command[:2] == ["git", "tag"] for command in commands)


def test_create_release_pushes_tag_to_origin() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _create_release("v1.0.0", "notes")
    commands = [invocation[0][0] for invocation in mock_run.call_args_list]
    assert any(command[:3] == ["git", "push", "origin"] for command in commands)


def test_create_release_calls_gh_release_create() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _create_release("v1.0.0", "notes")
    commands = [invocation[0][0] for invocation in mock_run.call_args_list]
    assert any(command[0] == "gh" for command in commands)


def test_create_release_passes_notes_to_gh() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _create_release("v1.0.0", "my release notes")
    gh_cmd = next(
        invocation[0][0] for invocation in mock_run.call_args_list if invocation[0][0][0] == "gh"
    )
    assert "my release notes" in gh_cmd


def test_create_release_order_is_tag_push_gh() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _create_release("v1.0.0", "notes")
    first_args = [invocation[0][0][0] for invocation in mock_run.call_args_list]
    assert first_args == ["git", "git", "gh"]


def test_check_gh_auth_exits_when_gh_not_installed() -> None:
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(SystemExit) as raised,
    ):
        _check_gh_auth()
    assert raised.value.code == 1


def test_check_gh_auth_exits_when_not_authenticated() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run") as mock_run,
        pytest.raises(SystemExit) as raised,
    ):
        mock_run.return_value = MagicMock(returncode=1)
        _check_gh_auth()
    assert raised.value.code == 1


def test_check_gh_auth_passes_when_authenticated() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        _check_gh_auth()


def test_check_gh_auth_runs_gh_auth_status() -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        _check_gh_auth()
    args = mock_run.call_args[0][0]
    assert args == ["gh", "auth", "status"]


def test_main_dry_run_prints_version_and_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--dry-run"])
    main(root=tmp_path)
    out = capsys.readouterr().out
    assert "1.2.3" in out
    assert "v1.2.3" in out


def test_main_dry_run_does_not_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--dry-run"])
    with patch("release._commit_version_bump") as mock_commit:
        main(root=tmp_path)
    mock_commit.assert_not_called()


def test_main_dry_run_does_not_call_create_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--dry-run"])
    with patch("release._create_release") as mock_create:
        main(root=tmp_path)
    mock_create.assert_not_called()


def test_main_without_release_flag_does_not_create_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._create_release") as mock_create:
        main(root=tmp_path)
    mock_create.assert_not_called()


def test_main_without_release_does_not_check_gh_auth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._check_gh_auth") as mock_auth:
        main(root=tmp_path)
    mock_auth.assert_not_called()


def test_main_with_release_checks_auth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--release"])
    with (
        patch("release._check_gh_auth") as mock_auth,
        patch("release._tag_exists", return_value=False),
        patch("release._create_release"),
    ):
        main(root=tmp_path)
    mock_auth.assert_called_once()


def test_main_with_release_aborts_when_tag_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--release"])
    with (
        patch("release._check_gh_auth"),
        patch("release._tag_exists", return_value=True),
        pytest.raises(SystemExit) as raised,
    ):
        main(root=tmp_path)
    assert raised.value.code == 1


def test_main_with_release_creates_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--release"])
    with (
        patch("release._check_gh_auth"),
        patch("release._tag_exists", return_value=False),
        patch("release._create_release") as mock_create,
    ):
        main(root=tmp_path)
    mock_create.assert_called_once()
    assert mock_create.call_args[0][0] == "v1.2.3"


def test_main_with_release_passes_changelog_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py", "--release"])
    with (
        patch("release._check_gh_auth"),
        patch("release._tag_exists", return_value=False),
        patch("release._create_release") as mock_create,
    ):
        main(root=tmp_path)
    notes_arg = mock_create.call_args[0][1]
    assert "new feature" in notes_arg
    assert "bug fix" not in notes_arg


def test_main_commits_when_pyproject_version_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._commit_version_bump") as mock_commit:
        main(root=tmp_path)
    mock_commit.assert_called_once()


def test_main_commits_when_readme_badge_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    (tmp_path / "README.md").write_text(_README_WITH_OLD_BADGE, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._commit_version_bump") as mock_commit:
        main(root=tmp_path)
    mock_commit.assert_called_once()


def test_main_skips_commit_when_nothing_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    (tmp_path / "README.md").write_text(_README_WITH_CURRENT_BADGE, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._commit_version_bump") as mock_commit:
        main(root=tmp_path)
    mock_commit.assert_not_called()


def test_main_updates_pyproject_from_changelog_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_OUTDATED, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._commit_version_bump"):
        main(root=tmp_path)
    assert 'version = "1.2.3"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")


def test_main_updates_readme_badge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT_CURRENT, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(_CHANGELOG, encoding="utf-8")
    (tmp_path / "README.md").write_text(_README_WITH_OLD_BADGE, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["release.py"])
    with patch("release._commit_version_bump"):
        main(root=tmp_path)
    assert "v1.2.3" in (tmp_path / "README.md").read_text(encoding="utf-8")
