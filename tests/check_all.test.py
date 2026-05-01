from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from check_all import (
    _collect,
    _load_config,
    _print_summary,
    _run,
    _run_on_dir,
    _run_on_files,
    main,
)


def _make_files(tmp_path: Path, names: list[str]) -> list[Path]:
    files = []
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        files.append(path)
    return files


def _write_config(tmp_path: Path, data: dict[str, object]) -> None:
    (tmp_path / ".dev-quality.yaml").write_text(yaml.dump(data), encoding="utf-8")


def _stub_collect(tmp_path: Path, py: list[str] = (), sh: list[str] = ()):
    py_files = [tmp_path / n for n in py]
    sh_files = [tmp_path / n for n in sh]

    def impl(root: Path, suffixes: frozenset[str]) -> list[Path]:
        if ".py" in suffixes:
            return list(py_files)
        return list(sh_files)

    return impl


# --- _collect ---


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


def test_collect_uses_git_ls_files_in_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t.com"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    (tmp_path / "tracked.py").write_text("x = 1\n")
    subprocess.run(
        ["git", "add", "tracked.py"], cwd=str(tmp_path), check=True, capture_output=True,
    )
    (tmp_path / "untracked.py").write_text("x = 1\n")
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "ignored.py").write_text("x = 1\n")
    result = _collect(tmp_path, frozenset([".py"]))
    names = {p.name for p in result}
    assert "tracked.py" in names
    assert "untracked.py" in names
    assert "ignored.py" not in names


# --- _load_config ---


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


# --- _run ---


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
    env_passed = mock_run.call_args[1]["env"]
    assert env_passed["MY_VAR"] == "value"
    assert "PATH" in env_passed


def test_run_no_extra_env_passes_none() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run(["cmd"])
    assert mock_run.call_args[1].get("env") is None


# --- _run_on_files ---


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
    env_passed = mock_run.call_args[1]["env"]
    assert env_passed["CHECK_COMPLEXITY_MAX"] == "8"


# --- _run_on_dir ---


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
    env_passed = mock_run.call_args[1]["env"]
    assert env_passed["MY_VAR"] == "x"


# --- _print_summary ---


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
    lines = [l for l in out.splitlines() if "Result" in l]
    assert lines
    assert "PASS" in lines[0]


def test_print_summary_result_fail_aggregates_total(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary({"a": (False, 2), "b": (False, 1)})
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if "Result" in l]
    assert lines
    assert "3" in lines[0]


# --- main() ---


def test_main_exits_0_when_all_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code == 0


def test_main_exits_1_when_any_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    fail = MagicMock(returncode=1, stdout="ABBREV:bad.py:1:ext", stderr="")
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["bad.py"])):
        with patch("subprocess.run", side_effect=[fail] + [ok] * 20):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code == 1


def test_main_uses_cwd_when_no_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all"])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", return_value=[]):
        with patch("subprocess.run", return_value=ok):
            with pytest.raises(SystemExit) as raised:
                main()
    assert raised.value.code in (0, 1)


def test_main_always_runs_shellcheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert any("shellcheck" in cmd for cmd in called_commands)


def test_main_skips_py_tools_when_no_py_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("ruff" in cmd for cmd in called_commands)
    assert not any("mypy" in cmd for cmd in called_commands)


def test_main_skip_config_prevents_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["mypy", "vulture"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("mypy" in cmd for cmd in called_commands)
    assert not any("vulture" in cmd for cmd in called_commands)


def test_main_line_length_passed_to_ruff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"line_length": 120})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    all_args = [arg for call in mock_run.call_args_list for arg in call[0][0]]
    assert "120" in all_args


def test_main_max_complexity_passed_as_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"max_complexity": 10})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    envs_seen: list[dict[str, str]] = []

    def capture_run(cmd: list[str], **kwargs: object) -> MagicMock:
        if kwargs.get("env"):
            envs_seen.append(dict(kwargs["env"]))  # type: ignore[arg-type]
        return ok

    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])):
        with patch("subprocess.run", side_effect=capture_run):
            with pytest.raises(SystemExit):
                main()
    assert any(env.get("CHECK_COMPLEXITY_MAX") == "10" for env in envs_seen)


def test_main_size_config_passed_as_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"max_file_lines": 500, "max_func_lines": 40})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    envs_seen: list[dict[str, str]] = []

    def capture_run(cmd: list[str], **kwargs: object) -> MagicMock:
        if kwargs.get("env"):
            envs_seen.append(dict(kwargs["env"]))  # type: ignore[arg-type]
        return ok

    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", side_effect=capture_run):
            with pytest.raises(SystemExit):
                main()
    assert any(env.get("CHECK_SIZE_MAX_FILE") == "500" for env in envs_seen)
    assert any(env.get("CHECK_SIZE_MAX_FUNC") == "40" for env in envs_seen)


def test_main_skip_custom_file_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["check-abbrev"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("check-abbrev" in cmd for cmd in called_commands)


def test_main_skip_custom_dir_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["check-bash-logs"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("check-bash-logs" in cmd for cmd in called_commands)


def test_main_skip_ruff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["ruff"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("ruff" in cmd for cmd in called_commands)


def test_main_skip_bandit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["bandit"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("bandit" in cmd for cmd in called_commands)


def test_main_skip_pylint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["pylint"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("pylint" in cmd for cmd in called_commands)


def test_main_python_version_passed_to_mypy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"python_version": "3.12"})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    all_args = [arg for call in mock_run.call_args_list for arg in call[0][0]]
    assert "3.12" in all_args


def test_main_ruff_check_ignores_s101(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok) as mock_run:
            with pytest.raises(SystemExit):
                main()
    ruff_check_calls = [
        call[0][0]
        for call in mock_run.call_args_list
        if call[0][0] and call[0][0][0] == "ruff" and "check" in call[0][0]
    ]
    assert ruff_check_calls
    args = ruff_check_calls[0]
    assert "--extend-ignore" in args
    idx = args.index("--extend-ignore")
    assert args[idx + 1] == "S101"


def test_main_prints_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])):
        with patch("subprocess.run", return_value=ok):
            with pytest.raises(SystemExit):
                main()
    out = capsys.readouterr().out
    assert "Result" in out
    assert "PASS" in out


def test_main_prints_summary_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    fail = MagicMock(returncode=1, stdout="error line", stderr="")
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["bad.py"])):
        with patch("subprocess.run", side_effect=[fail] + [ok] * 20):
            with pytest.raises(SystemExit):
                main()
    out = capsys.readouterr().out
    assert "Result" in out
    assert "FAIL" in out
