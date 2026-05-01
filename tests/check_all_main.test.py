from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from check_all import (
    _semgrep_config,
    main,
)
from conftest import _stub_collect, _write_config


def test_main_exits_0_when_all_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit) as raised,
    ):
        main()
    assert raised.value.code == 0


def test_main_exits_1_when_any_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    fail = MagicMock(returncode=1, stdout="ABBREV:bad.py:1:ext", stderr="")
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["bad.py"])),
        patch("subprocess.run", side_effect=[fail] + [ok] * 20),
        pytest.raises(SystemExit) as raised,
    ):
        main()
    assert raised.value.code == 1


def test_main_uses_cwd_when_no_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all"])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", return_value=[]),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit) as raised,
    ):
        main()
    assert raised.value.code in (0, 1)


def test_main_always_runs_shellcheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert any("shellcheck" in command for command in called_commands)


def test_main_skips_py_tools_when_no_py_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("ruff" in command for command in called_commands)
    assert not any("mypy" in command for command in called_commands)


def test_main_skip_config_prevents_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["mypy", "vulture"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("mypy" in command for command in called_commands)
    assert not any("vulture" in command for command in called_commands)


def test_main_line_length_passed_to_ruff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"line_length": 120})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
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
    environments_seen: list[dict[str, str]] = []

    def capture_run(command: list[str], **kwargs: object) -> MagicMock:
        if kwargs.get("env"):
            environments_seen.append(dict(kwargs["env"]))  # type: ignore[call-overload]
        return ok

    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])),
        patch("subprocess.run", side_effect=capture_run),
        pytest.raises(SystemExit),
    ):
        main()
    assert any(environ.get("CHECK_COMPLEXITY_MAX") == "10" for environ in environments_seen)


def test_main_size_config_passed_as_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"max_file_lines": 500, "max_func_lines": 40})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    environments_seen: list[dict[str, str]] = []

    def capture_run(command: list[str], **kwargs: object) -> MagicMock:
        if kwargs.get("env"):
            environments_seen.append(dict(kwargs["env"]))  # type: ignore[call-overload]
        return ok

    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", side_effect=capture_run),
        pytest.raises(SystemExit),
    ):
        main()
    assert any(environ.get("CHECK_SIZE_MAX_FILE") == "500" for environ in environments_seen)
    assert any(environ.get("CHECK_SIZE_MAX_FUNC") == "40" for environ in environments_seen)


def test_main_skip_custom_file_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["check-abbrev"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("check-abbrev" in command for command in called_commands)


def test_main_skip_custom_dir_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["check-bash-logs"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, sh=["script.sh"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("check-bash-logs" in command for command in called_commands)


def test_main_skip_ruff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["ruff"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("ruff" in command for command in called_commands)


def test_main_skip_bandit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["bandit"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("bandit" in command for command in called_commands)


def test_main_skip_pylint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"skip": ["pylint"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0] for call in mock_run.call_args_list]
    assert not any("pylint" in command for command in called_commands)


def test_main_python_version_passed_to_mypy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"python_version": "3.12"})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    all_args = [arg for call in mock_run.call_args_list for arg in call[0][0]]
    assert "3.12" in all_args


def test_main_prints_scanning_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", return_value=[]),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit),
    ):
        main()
    assert str(tmp_path.resolve()) in capsys.readouterr().out


def test_main_clear_cache_does_not_print_scanning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--clear-cache"])
    with pytest.raises(SystemExit):
        main()
    assert "Scanning" not in capsys.readouterr().out


def test_main_clear_cache_removes_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "ruff").mkdir()
    monkeypatch.setattr(sys, "argv", ["check-all", "--clear-cache"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert not cache.exists()


def test_main_clear_cache_when_nothing_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--clear-cache"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert "No cache" in capsys.readouterr().out


def test_main_clear_cache_prints_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(sys, "argv", ["check-all", "--clear-cache"])
    with pytest.raises(SystemExit):
        main()
    assert str(cache) in capsys.readouterr().out


def test_main_prints_cache_hint_after_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit),
    ):
        main()
    out = capsys.readouterr().out
    assert str(tmp_path / "cache") in out
    assert "--clear-cache" in out
    assert "--no-cache" in out


def test_main_no_cache_flag_omits_cache_hint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--no-cache", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit),
    ):
        main()
    assert "--clear-cache" not in capsys.readouterr().out


def test_main_ruff_default_uses_cache_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    ruff_calls = [call[0][0] for call in mock_run.call_args_list if call[0][0][0] == "ruff"]
    assert ruff_calls
    assert all("--cache-dir" in args for args in ruff_calls)
    assert not any("--no-cache" in args for args in ruff_calls)


def test_main_mypy_default_uses_cache_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    mypy_calls = [call[0][0] for call in mock_run.call_args_list if call[0][0][0] == "mypy"]
    assert mypy_calls
    assert "--cache-dir" in mypy_calls[0]
    assert "--no-incremental" not in mypy_calls[0]


def test_main_no_cache_flag_disables_ruff_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--no-cache", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    ruff_calls = [call[0][0] for call in mock_run.call_args_list if call[0][0][0] == "ruff"]
    assert ruff_calls
    assert all("--no-cache" in args for args in ruff_calls)
    assert not any("--cache-dir" in args for args in ruff_calls)


def test_main_no_cache_flag_disables_mypy_incremental(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--no-cache", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    mypy_calls = [call[0][0] for call in mock_run.call_args_list if call[0][0][0] == "mypy"]
    assert mypy_calls
    assert "--no-incremental" in mypy_calls[0]
    assert "--cache-dir" not in mypy_calls[0]


def test_main_no_cache_flag_resolves_path_correctly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "--no-cache", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", return_value=[]) as mock_collect,
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit),
    ):
        main()
    assert mock_collect.call_args[0][0] == tmp_path.resolve()


def test_main_ruff_check_ignores_s101(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    ruff_check_calls = [
        call[0][0]
        for call in mock_run.call_args_list
        if call[0][0] and call[0][0][0] == "ruff" and "check" in call[0][0]
    ]
    assert ruff_check_calls
    args = ruff_check_calls[0]
    assert "--extend-ignore" in args
    position = args.index("--extend-ignore")
    assert "S101" in args[position + 1]


def test_main_prints_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok),
        pytest.raises(SystemExit),
    ):
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
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["bad.py"])),
        patch("subprocess.run", side_effect=[fail] + [ok] * 20),
        pytest.raises(SystemExit),
    ):
        main()
    out = capsys.readouterr().out
    assert "Result" in out
    assert "FAIL" in out


def test_semgrep_config_returns_none_when_no_rules(tmp_path: Path) -> None:
    assert _semgrep_config(tmp_path) is None


def test_semgrep_config_returns_semgrep_dir_when_yml_present(tmp_path: Path) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    assert _semgrep_config(tmp_path) == semgrep_dir


def test_semgrep_config_returns_semgrep_dir_when_yaml_present(tmp_path: Path) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yaml").write_text("rules: []", encoding="utf-8")
    assert _semgrep_config(tmp_path) == semgrep_dir


def test_semgrep_config_returns_none_when_dir_is_empty(tmp_path: Path) -> None:
    (tmp_path / ".semgrep").mkdir()
    assert _semgrep_config(tmp_path) is None


def test_semgrep_config_returns_semgrep_yml_at_root(tmp_path: Path) -> None:
    (tmp_path / "semgrep.yml").write_text("rules: []", encoding="utf-8")
    assert _semgrep_config(tmp_path) == tmp_path / "semgrep.yml"


def test_semgrep_config_returns_semgrep_yaml_at_root(tmp_path: Path) -> None:
    (tmp_path / "semgrep.yaml").write_text("rules: []", encoding="utf-8")
    assert _semgrep_config(tmp_path) == tmp_path / "semgrep.yaml"


def test_main_semgrep_runs_when_rules_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=ok) as mock_run,
        patch("check_all.shutil.which", return_value="/usr/bin/semgrep"),
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0][0] for call in mock_run.call_args_list if call[0][0]]
    assert "semgrep" in called_commands


def test_main_semgrep_skipped_when_no_rules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0][0] for call in mock_run.call_args_list if call[0][0]]
    assert "semgrep" not in called_commands


def test_main_semgrep_skipped_when_not_in_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=ok) as mock_run,
        patch("check_all.shutil.which", return_value=None),
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0][0] for call in mock_run.call_args_list if call[0][0]]
    assert "semgrep" not in called_commands


def test_main_skip_semgrep_via_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    _write_config(tmp_path, {"skip": ["semgrep"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=ok) as mock_run,
        patch("check_all.shutil.which", return_value="/usr/bin/semgrep"),
        pytest.raises(SystemExit),
    ):
        main()
    called_commands = [call[0][0][0] for call in mock_run.call_args_list if call[0][0]]
    assert "semgrep" not in called_commands


def test_main_semgrep_uses_config_arg(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=ok) as mock_run,
        patch("check_all.shutil.which", return_value="/usr/bin/semgrep"),
        pytest.raises(SystemExit),
    ):
        main()
    semgrep_calls = [call[0][0] for call in mock_run.call_args_list if call[0][0][0] == "semgrep"]
    assert semgrep_calls
    args = semgrep_calls[0]
    assert "--config" in args
    config_position = args.index("--config")
    assert args[config_position + 1] == str(semgrep_dir)


def test_main_semgrep_exits_1_on_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semgrep_dir = tmp_path / ".semgrep"
    semgrep_dir.mkdir()
    (semgrep_dir / "rules.yml").write_text("rules: []", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    fail = MagicMock(returncode=1, stdout="Finding: bad.py:10", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path)),
        patch("subprocess.run", return_value=fail),
        patch("check_all.shutil.which", return_value="/usr/bin/semgrep"),
        pytest.raises(SystemExit) as raised,
    ):
        main()
    assert raised.value.code == 1


def test_main_ruff_check_has_per_file_ignores_for_plr2004(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, py=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    ruff_check_calls = [
        call[0][0]
        for call in mock_run.call_args_list
        if call[0][0] and call[0][0][0] == "ruff" and "check" in call[0][0]
    ]
    assert ruff_check_calls
    args = ruff_check_calls[0]
    per_file_positions = [index for index, arg in enumerate(args) if arg == "--per-file-ignores"]
    per_file_values = [args[index + 1] for index in per_file_positions]
    assert any("PLR2004" in value for value in per_file_values)


def test_install_skill_subcommand_calls_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "install-skill", "--target", str(tmp_path)])
    with (
        patch("check_all._do_install_skill") as mock_install,
        pytest.raises(SystemExit) as raised,
    ):
        main()
    mock_install.assert_called_once_with(str(tmp_path))
    assert raised.value.code == 0


def test_install_skill_subcommand_exits_1_when_target_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "install-skill"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "--target" in capsys.readouterr().out


def test_install_skill_subcommand_exits_1_when_target_flag_has_no_value(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check-all", "install-skill", "--target"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "--target" in capsys.readouterr().out


def test_do_install_skill_writes_skill_md(tmp_path: Path) -> None:
    from check_all import _do_install_skill

    _do_install_skill(str(tmp_path))
    assert (tmp_path / "dev-quality" / "SKILL.md").exists()
