from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import check_bash_logs as module
from check_bash_logs import _has_log_init, _script_needs_log, check_bash_logs, main


def touch(path: Path, content: str = "#!/usr/bin/env bash") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def script_with_log(path: Path) -> None:
    touch(path, '#!/usr/bin/env bash\nlog::init_script "test"\n')


def test_returns_none_when_scripts_bash_missing(tmp_path: Path) -> None:
    assert check_bash_logs(tmp_path) is None


def test_pass_when_script_has_log_init(tmp_path: Path) -> None:
    script_with_log(tmp_path / "scripts/bash/foo.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "PASS:bash-logs" in result


def test_missing_log_reported(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "MISSING_LOG:scripts/bash/foo.sh" in result


def test_hooks_are_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/hooks/pre-commit.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "PASS:bash-logs" in result


def test_tests_are_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/tests/foo.test.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "PASS:bash-logs" in result


def test_lib_scripts_are_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/lib/helper.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "PASS:bash-logs" in result


def test_statusline_is_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/statusline.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "PASS:bash-logs" in result


def test_multiple_missing_all_reported(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    touch(tmp_path / "scripts/bash/bar.sh")
    result = check_bash_logs(tmp_path)
    assert result is not None
    assert "MISSING_LOG:scripts/bash/foo.sh" in result
    assert "MISSING_LOG:scripts/bash/bar.sh" in result


def test_has_log_init_true(tmp_path: Path) -> None:
    script = tmp_path / "foo.sh"
    script.write_text('log::init_script "test"\n', encoding="utf-8")
    assert _has_log_init(script) is True


def test_has_log_init_false(tmp_path: Path) -> None:
    script = tmp_path / "foo.sh"
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    assert _has_log_init(script) is False


def test_script_needs_log_exempt_dir(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    script = scripts_dir / "hooks/pre-commit.sh"
    script.parent.mkdir(parents=True)
    script.touch()
    assert _script_needs_log(script, scripts_dir) is False


def test_script_needs_log_exempt_name(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    script = scripts_dir / "statusline.sh"
    script.touch()
    assert _script_needs_log(script, scripts_dir) is False


def test_script_needs_log_regular(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    script = scripts_dir / "deploy.sh"
    script.touch()
    assert _script_needs_log(script, scripts_dir) is True


def test_main_exits_0_on_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script_with_log(tmp_path / "scripts/bash/foo.sh")
    monkeypatch.setattr(sys, "argv", ["check_bash_logs.py", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert "PASS:bash-logs" in capsys.readouterr().out


def test_main_exits_1_on_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    monkeypatch.setattr(sys, "argv", ["check_bash_logs.py", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1


def test_main_exits_0_when_no_bash_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_bash_logs.py", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert capsys.readouterr().out == ""


def test_find_root_falls_back_to_cwd_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_error(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(subprocess, "run", raise_error)
    result = module._find_root()
    assert result == Path.cwd()


def test_main_no_args_uses_find_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_bash_logs.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code in (0, 1)
