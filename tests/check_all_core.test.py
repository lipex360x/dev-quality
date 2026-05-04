from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from check_all import (
    _collect,
    _load_config,
    _print_summary,
    _run,
    _run_on_dir,
    _run_on_files,
    _user_cache_dir,
    _warn_if_precommit_outdated,
)
from conftest import _make_files, _write_config


def test_collect_finds_py_and_sh(tmp_path: Path) -> None:
    _make_files(tmp_path, ["a.py", "b.sh", "c.txt"])
    result = _collect(tmp_path, frozenset([".py", ".sh"]))
    names = {file_path.name for file_path in result}
    assert "a.py" in names
    assert "b.sh" in names
    assert "c.txt" not in names


def test_collect_skips_venv(tmp_path: Path) -> None:
    _make_files(tmp_path, [".venv/lib/foo.py", "src/bar.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {file_path.name for file_path in result}
    assert "foo.py" not in names
    assert "bar.py" in names


def test_collect_skips_pycache(tmp_path: Path) -> None:
    _make_files(tmp_path, ["__pycache__/foo.pyc", "src/ok.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {file_path.name for file_path in result}
    assert "ok.py" in names


def test_collect_skips_git(tmp_path: Path) -> None:
    _make_files(tmp_path, [".git/hooks/pre-commit", "ok.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {file_path.name for file_path in result}
    assert "ok.py" in names
    assert "pre-commit" not in names


def test_collect_returns_sorted(tmp_path: Path) -> None:
    _make_files(tmp_path, ["z.py", "a.py", "m.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = [file_path.name for file_path in result]
    assert names == sorted(names)


def test_collect_uses_git_ls_files_in_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(
        ["git", "config", "user.email", "t@t.com"],  # noqa: S607
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],  # noqa: S607
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    (tmp_path / "tracked.py").write_text("x = 1\n")
    subprocess.run(
        ["git", "add", "tracked.py"],  # noqa: S607
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    (tmp_path / "untracked.py").write_text("x = 1\n")
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "ignored.py").write_text("x = 1\n")
    result = _collect(tmp_path, frozenset([".py"]))
    names = {file_path.name for file_path in result}
    assert "tracked.py" in names
    assert "untracked.py" in names
    assert "ignored.py" not in names


def test_collect_skips_staged_but_deleted_from_disk(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(
        ["git", "config", "user.email", "t@t.com"],  # noqa: S607
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],  # noqa: S607
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    ghost = tmp_path / "ghost.sh"
    ghost.write_text("#!/bin/bash\n")
    subprocess.run(["git", "add", "ghost.sh"], cwd=str(tmp_path), check=True, capture_output=True)  # noqa: S607
    ghost.unlink()
    result = _collect(tmp_path, frozenset([".sh"]))
    assert all(file_path.name != "ghost.sh" for file_path in result)


def test_load_config_returns_empty_when_no_file(tmp_path: Path) -> None:
    assert _load_config(tmp_path) == {}


def test_load_config_returns_empty_for_empty_file(tmp_path: Path) -> None:
    (tmp_path / ".dev-quality.yaml").write_text("", encoding="utf-8")
    assert _load_config(tmp_path) == {}


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    _write_config(tmp_path, {"line_length": 120, "skip": ["mypy"]})
    config = _load_config(tmp_path)
    assert config["line_length"] == 120
    assert config["skip"] == ["mypy"]


def test_run_returns_code_and_output() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        code, output = _run(["echo", "ok"])
    assert code == 0
    assert output == "ok"


def test_run_combines_stdout_and_stderr() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="out", stderr="err")
        code, output = _run(["cmd"])
    assert code == 1
    assert "out" in output
    assert "err" in output


def test_run_passes_extra_env() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run(["cmd"], {"MY_VAR": "value"})
    environ_passed = mock_run.call_args[1]["env"]
    assert environ_passed["MY_VAR"] == "value"
    assert "PATH" in environ_passed


def test_run_no_extra_env_passes_none() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run(["cmd"])
    assert mock_run.call_args[1].get("env") is None


def test_run_on_files_skips_when_empty(tmp_path: Path) -> None:
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        result = _run_on_files(["check-abbrev"], [], findings)
    mock_run.assert_not_called()
    assert result is True
    assert findings == []


def test_run_on_files_passes_files_to_command(tmp_path: Path) -> None:
    files = _make_files(tmp_path, ["a.py"])
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_on_files(["check-abbrev"], files, findings)
    called_args = mock_run.call_args[0][0]
    assert str(files[0]) in called_args


def test_run_on_files_returns_false_on_nonzero(tmp_path: Path) -> None:
    files = _make_files(tmp_path, ["a.py"])
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="ABBREV:a.py:1:ext", stderr="")
        result = _run_on_files(["check-abbrev"], files, findings)
    assert result is False
    assert "ABBREV:a.py:1:ext" in findings


def test_run_on_files_passes_extra_env(tmp_path: Path) -> None:
    files = _make_files(tmp_path, ["a.sh"])
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_on_files(["check-complexity"], files, findings, {"CHECK_COMPLEXITY_MAX": "8"})
    environ_passed = mock_run.call_args[1]["env"]
    assert environ_passed["CHECK_COMPLEXITY_MAX"] == "8"


def test_run_on_dir_passes_root(tmp_path: Path) -> None:
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_on_dir(["check-bash-logs"], tmp_path, findings)
    called_args = mock_run.call_args[0][0]
    assert str(tmp_path) in called_args


def test_run_on_dir_returns_false_on_nonzero(tmp_path: Path) -> None:
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="MISSING_LOG:foo.sh", stderr="")
        result = _run_on_dir(["check-bash-logs"], tmp_path, findings)
    assert result is False
    assert "MISSING_LOG:foo.sh" in findings


def test_run_on_dir_passes_extra_env(tmp_path: Path) -> None:
    findings: list[str] = []
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_on_dir(["check-bash-logs"], tmp_path, findings, {"MY_VAR": "x"})
    environ_passed = mock_run.call_args[1]["env"]
    assert environ_passed["MY_VAR"] == "x"


def test_print_summary_empty_is_noop(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({})
    assert capsys.readouterr().out == ""


def test_print_summary_shows_pass(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"check-abbrev": (True, 0), "mypy": (True, 0)})
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "Result" in out


def test_print_summary_shows_fail_with_count(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"check-abbrev": (False, 3), "mypy": (True, 0)})
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "3" in out
    assert "Result" in out


def test_print_summary_singular_issue(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"mypy": (False, 1)})
    out = capsys.readouterr().out
    assert "1 issue" in out


def test_print_summary_plural_issues(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"mypy": (False, 2)})
    out = capsys.readouterr().out
    assert "2 issues" in out


def test_print_summary_result_pass_when_all_pass(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"a": (True, 0), "b": (True, 0)})
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if "Result" in line]
    assert lines
    assert "PASS" in lines[0]


def test_print_summary_result_fail_aggregates_total(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"a": (False, 2), "b": (False, 1)})
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if "Result" in line]
    assert lines
    assert "3" in lines[0]


def test_user_cache_dir_returns_path_under_tmp() -> None:
    result = _user_cache_dir()
    assert result == Path(tempfile.gettempdir()) / "dev-quality"


def _write_precommit_config(directory: Path, repo_url: str, revision: str) -> None:
    content = (
        f"repos:\n  - repo: {repo_url}\n    rev: {revision}\n    hooks:\n      - id: check-all\n"
    )
    (directory / ".pre-commit-config.yaml").write_text(content, encoding="utf-8")


def test_warn_if_precommit_outdated_warns_when_rev_is_old(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_precommit_config(tmp_path, "https://github.com/lipex360x/dev-quality", "v0.7.0")
    with patch("importlib.metadata.version", return_value="0.8.1"):
        _warn_if_precommit_outdated(tmp_path)
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "v0.7.0" in out
    assert "v0.8.1" in out
    assert "pre-commit autoupdate" in out


def test_warn_if_precommit_outdated_silent_when_rev_matches(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_precommit_config(tmp_path, "https://github.com/lipex360x/dev-quality", "v0.8.1")
    with patch("importlib.metadata.version", return_value="0.8.1"):
        _warn_if_precommit_outdated(tmp_path)
    assert capsys.readouterr().out == ""


def test_warn_if_precommit_outdated_silent_when_no_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _warn_if_precommit_outdated(tmp_path)
    assert capsys.readouterr().out == ""


def test_warn_if_precommit_outdated_silent_when_different_repo(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_precommit_config(tmp_path, "https://github.com/psf/black", "24.0.0")
    with patch("importlib.metadata.version", return_value="0.8.1"):
        _warn_if_precommit_outdated(tmp_path)
    assert capsys.readouterr().out == ""


def test_warn_if_precommit_outdated_silent_on_malformed_yaml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text(":", encoding="utf-8")
    _warn_if_precommit_outdated(tmp_path)
    assert capsys.readouterr().out == ""
