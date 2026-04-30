from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import check_bash_tests as module
from check_bash_tests import _script_is_covered, check_bash_tests, main


def touch(path: Path, content: str = "#!/usr/bin/env bash") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_returns_none_when_scripts_bash_missing(tmp_path: Path) -> None:
    assert check_bash_tests(tmp_path) is None


def test_pass_when_all_scripts_have_tests(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    touch(tmp_path / "scripts/bash/tests/foo.test.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "PASS:bash-tests" in result


def test_missing_test_reported(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "MISSING_TEST:scripts/bash/foo.sh" in result


def test_hooks_are_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/hooks/pre-commit.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "PASS:bash-tests" in result


def test_test_files_are_exempt(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/tests/foo.test.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "PASS:bash-tests" in result


def test_lib_scripts_are_checked(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/lib/helper.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "MISSING_TEST:scripts/bash/lib/helper.sh" in result


def test_lib_script_passes_when_test_exists(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/lib/helper.sh")
    touch(tmp_path / "scripts/bash/tests/helper.test.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "PASS:bash-tests" in result


def test_multiple_missing_all_reported(tmp_path: Path) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    touch(tmp_path / "scripts/bash/bar.sh")
    result = check_bash_tests(tmp_path)
    assert result is not None
    assert "MISSING_TEST:scripts/bash/foo.sh" in result
    assert "MISSING_TEST:scripts/bash/bar.sh" in result


def test_script_is_covered_exempt_dir(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    tests_dir = scripts_dir / "tests"
    script = scripts_dir / "hooks/pre-commit.sh"
    script.parent.mkdir(parents=True)
    script.touch()
    assert _script_is_covered(script, scripts_dir, tests_dir) is True


def test_script_is_covered_test_exists(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    tests_dir = scripts_dir / "tests"
    tests_dir.mkdir(parents=True)
    script = scripts_dir / "foo.sh"
    script.touch()
    (tests_dir / "foo.test.sh").touch()
    assert _script_is_covered(script, scripts_dir, tests_dir) is True


def test_script_is_covered_no_test(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts/bash"
    scripts_dir.mkdir(parents=True)
    tests_dir = scripts_dir / "tests"
    script = scripts_dir / "foo.sh"
    script.touch()
    assert _script_is_covered(script, scripts_dir, tests_dir) is False


def test_main_exits_0_on_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    touch(tmp_path / "scripts/bash/tests/foo.test.sh")
    monkeypatch.setattr(sys, "argv", ["check_bash_tests.py", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert "PASS:bash-tests" in capsys.readouterr().out


def test_main_exits_1_on_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    touch(tmp_path / "scripts/bash/foo.sh")
    monkeypatch.setattr(sys, "argv", ["check_bash_tests.py", str(tmp_path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1


def test_main_exits_0_when_no_bash_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_bash_tests.py", str(tmp_path)])
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
    monkeypatch.setattr(sys, "argv", ["check_bash_tests.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code in (0, 1)
