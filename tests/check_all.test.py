from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from check_all import _collect, _run, _run_on_dir, _run_on_files, main


def _make_files(tmp_path: Path, names: list[str]) -> list[Path]:
    files = []
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        files.append(path)
    return files


def test_collect_finds_py_and_sh(tmp_path: Path) -> None:
    _make_files(tmp_path, ["a.py", "b.sh", "c.txt"])
    result = _collect(tmp_path, frozenset([".py", ".sh"]))
    names = {p.name for p in result}
    assert "a.py" in names
    assert "b.sh" in names
    assert "c.txt" not in names


def test_collect_skips_venv(tmp_path: Path) -> None:
    _make_files(tmp_path, [".venv/lib/foo.py", "src/bar.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {p.name for p in result}
    assert "foo.py" not in names
    assert "bar.py" in names


def test_collect_skips_pycache(tmp_path: Path) -> None:
    _make_files(tmp_path, ["__pycache__/foo.pyc", "src/ok.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {p.name for p in result}
    assert "ok.py" in names


def test_collect_skips_git(tmp_path: Path) -> None:
    _make_files(tmp_path, [".git/hooks/pre-commit", "ok.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = {p.name for p in result}
    assert "ok.py" in names
    assert "pre-commit" not in names


def test_collect_returns_sorted(tmp_path: Path) -> None:
    _make_files(tmp_path, ["z.py", "a.py", "m.py"])
    result = _collect(tmp_path, frozenset([".py"]))
    names = [p.name for p in result]
    assert names == sorted(names)


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


def test_main_exits_0_when_all_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "ok.py").touch()
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=ok):
        with patch("shutil.which", return_value="/usr/bin/shellcheck"):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code == 0


def test_main_exits_1_when_any_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "bad.py").touch()
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    fail = MagicMock(returncode=1, stdout="ABBREV:bad.py:1:ext", stderr="")
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", side_effect=[fail] + [ok] * 20):
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code == 1


def test_main_uses_cwd_when_no_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all"])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=ok):
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code in (0, 1)


def test_main_skips_shellcheck_when_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "script.sh").touch()
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=ok) as mock_run:
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("shellcheck" in cmd for cmd in called_commands)


def test_main_runs_shellcheck_when_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "script.sh").touch()
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=ok) as mock_run:
        with patch("shutil.which", return_value="/usr/bin/shellcheck"):
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert any("shellcheck" in cmd for cmd in called_commands)


def test_main_skips_py_tools_when_no_py_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "script.sh").touch()
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=ok) as mock_run:
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("ruff" in cmd for cmd in called_commands)
    assert not any("mypy" in cmd for cmd in called_commands)
