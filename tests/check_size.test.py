from __future__ import annotations

import sys
from pathlib import Path

import pytest
from check_size import _check_bash, _check_python, _is_test_file, _scan_file, main


def _py_lines(count: int) -> str:
    return "\n".join(f"x_{i} = {i}" for i in range(count)) + "\n"


def _py_func(name: str, count: int) -> str:
    body = "\n".join(f"    x_{i} = {i}" for i in range(count - 1))
    return f"def {name}():\n{body}\n"


def _bash_func(name: str, count: int) -> str:
    body = "\n".join(f"    echo {i}" for i in range(count - 2))
    return f"{name}() {{\n{body}\n}}\n"


def test_no_files_exits_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_size.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_py_clean_file(tmp_path: Path) -> None:
    source = tmp_path / "ok.py"
    source.write_text(_py_lines(5), encoding="utf-8")
    assert _check_python(source, 10, 5) == []


def test_py_file_exactly_max(tmp_path: Path) -> None:
    source = tmp_path / "max.py"
    source.write_text(_py_lines(10), encoding="utf-8")
    assert _check_python(source, 10, 5) == []


def test_py_file_too_long(tmp_path: Path) -> None:
    source = tmp_path / "big.py"
    source.write_text(_py_lines(11), encoding="utf-8")
    findings = _check_python(source, 10, 5)
    assert any("FILE_TOO_LONG" in finding for finding in findings)
    assert any("11" in finding for finding in findings)


def test_py_clean_function(tmp_path: Path) -> None:
    source = tmp_path / "ok.py"
    source.write_text(_py_func("small", 3), encoding="utf-8")
    assert _check_python(source, 100, 5) == []


def test_py_function_exactly_max(tmp_path: Path) -> None:
    source = tmp_path / "max.py"
    source.write_text(_py_func("at_limit", 5), encoding="utf-8")
    assert _check_python(source, 100, 5) == []


def test_py_function_too_long(tmp_path: Path) -> None:
    source = tmp_path / "big.py"
    source.write_text(_py_func("huge", 6), encoding="utf-8")
    findings = _check_python(source, 100, 5)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)
    assert any("huge" in finding for finding in findings)


def test_py_reports_function_line_number(tmp_path: Path) -> None:
    source = tmp_path / "lined.py"
    source.write_text(_py_func("big_func", 6), encoding="utf-8")
    findings = _check_python(source, 100, 5)
    assert any(":1:" in finding for finding in findings)


def test_py_read_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.py"
    findings = _check_python(missing, 100, 5)
    assert len(findings) == 1
    assert findings[0].startswith("READ_ERROR:")


def test_py_parse_error(tmp_path: Path) -> None:
    source = tmp_path / "bad.py"
    source.write_text("def foo(:\n    pass\n", encoding="utf-8")
    findings = _check_python(source, 100, 5)
    assert any("PARSE_ERROR" in finding for finding in findings)


def test_py_async_function_too_long(tmp_path: Path) -> None:
    body = "\n".join(f"    x_{i} = {i}" for i in range(5))
    source = tmp_path / "async.py"
    source.write_text(f"async def big_async():\n{body}\n", encoding="utf-8")
    findings = _check_python(source, 100, 5)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)


def test_py_func_no_end_lineno(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ast

    import check_size as module

    source = tmp_path / "ok.py"
    source.write_text("def foo():\n    pass\n", encoding="utf-8")

    original = module._func_finding

    def _patched(node: ast.FunctionDef | ast.AsyncFunctionDef, path: Path, max_func: int) -> str | None:
        node.end_lineno = None
        return original(node, path, max_func)  # type: ignore[no-any-return]

    monkeypatch.setattr(module, "_func_finding", _patched)
    findings = _check_python(source, 100, 5)
    assert findings == []


def test_bash_clean_file(tmp_path: Path) -> None:
    script = tmp_path / "ok.sh"
    script.write_text("#!/usr/bin/env bash\n" + "echo hi\n" * 5, encoding="utf-8")
    assert _check_bash(script, 10, 5) == []


def test_bash_file_exactly_max(tmp_path: Path) -> None:
    script = tmp_path / "max.sh"
    script.write_text("#!/usr/bin/env bash\n" + "echo hi\n" * 9, encoding="utf-8")
    assert _check_bash(script, 10, 5) == []


def test_bash_file_too_long(tmp_path: Path) -> None:
    script = tmp_path / "big.sh"
    script.write_text("#!/usr/bin/env bash\n" + "echo hi\n" * 10, encoding="utf-8")
    findings = _check_bash(script, 10, 5)
    assert any("FILE_TOO_LONG" in finding for finding in findings)


def test_bash_clean_function(tmp_path: Path) -> None:
    script = tmp_path / "ok.sh"
    script.write_text("#!/usr/bin/env bash\n" + _bash_func("small", 4), encoding="utf-8")
    assert _check_bash(script, 100, 5) == []


def test_bash_function_exactly_max(tmp_path: Path) -> None:
    script = tmp_path / "max.sh"
    script.write_text("#!/usr/bin/env bash\n" + _bash_func("at_limit", 5), encoding="utf-8")
    assert _check_bash(script, 100, 5) == []


def test_bash_function_too_long(tmp_path: Path) -> None:
    script = tmp_path / "big.sh"
    script.write_text("#!/usr/bin/env bash\n" + _bash_func("huge_func", 6), encoding="utf-8")
    findings = _check_bash(script, 100, 5)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)
    assert any("huge_func" in finding for finding in findings)


def test_bash_reports_function_line_number(tmp_path: Path) -> None:
    script = tmp_path / "lined.sh"
    script.write_text("#!/usr/bin/env bash\n" + _bash_func("big_func", 6), encoding="utf-8")
    findings = _check_bash(script, 100, 5)
    assert any(":2:" in finding for finding in findings)


def test_bash_single_line_function_not_flagged(tmp_path: Path) -> None:
    script = tmp_path / "oneliner.sh"
    script.write_text(
        '#!/usr/bin/env bash\n_log_fb() { printf "%s\\n" "$*"; }\nlog_info() { _log_fb INFO "$*"; }\n',
        encoding="utf-8",
    )
    assert _check_bash(script, 100, 5) == []


def test_bash_read_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sh"
    findings = _check_bash(missing, 100, 5)
    assert len(findings) == 1
    assert findings[0].startswith("READ_ERROR:")


def test_multiple_violations(tmp_path: Path) -> None:
    source = tmp_path / "multi.py"
    source.write_text(_py_lines(11) + _py_func("huge", 6), encoding="utf-8")
    findings = _check_python(source, 10, 5)
    assert any("FILE_TOO_LONG" in finding for finding in findings)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)


def test_scan_file_dispatches_sh(tmp_path: Path) -> None:
    script = tmp_path / "big.sh"
    script.write_text("#!/usr/bin/env bash\n" + _bash_func("huge", 6), encoding="utf-8")
    findings = _scan_file(script, 100, 5)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)


def test_scan_file_dispatches_py(tmp_path: Path) -> None:
    source = tmp_path / "big.py"
    source.write_text(_py_func("huge", 6), encoding="utf-8")
    findings = _scan_file(source, 100, 5)
    assert any("FUNC_TOO_LONG" in finding for finding in findings)


def test_main_dirty_exits_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "big.py"
    source.write_text(_py_func("huge", 6), encoding="utf-8")
    monkeypatch.setenv("CHECK_SIZE_MAX_FILE", "100")
    monkeypatch.setenv("CHECK_SIZE_MAX_FUNC", "5")
    monkeypatch.setattr(sys, "argv", ["check_size.py", str(source)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "FUNC_TOO_LONG" in capsys.readouterr().out


def test_main_clean_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "ok.py"
    source.write_text(_py_func("small", 3), encoding="utf-8")
    monkeypatch.setenv("CHECK_SIZE_MAX_FILE", "100")
    monkeypatch.setenv("CHECK_SIZE_MAX_FUNC", "5")
    monkeypatch.setattr(sys, "argv", ["check_size.py", str(source)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_is_test_file_from_tests_directory() -> None:
    assert _is_test_file(Path("tests/foo.test.py")) is True


def test_is_test_file_test_prefix() -> None:
    assert _is_test_file(Path("test_foo.py")) is True


def test_is_test_file_test_suffix() -> None:
    assert _is_test_file(Path("foo_test.py")) is True


def test_is_test_file_dot_test_suffix() -> None:
    assert _is_test_file(Path("foo.test.py")) is True


def test_is_test_file_conftest() -> None:
    assert _is_test_file(Path("conftest.py")) is True


def test_is_not_test_file_regular() -> None:
    assert _is_test_file(Path("foo.py")) is False


def test_main_test_file_at_900_below_test_limit_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    source = test_dir / "big_test.py"
    source.write_text(_py_lines(900), encoding="utf-8")
    monkeypatch.setenv("CHECK_SIZE_MAX_FILE", "800")
    monkeypatch.setenv("CHECK_SIZE_MAX_TEST_FILE", "1500")
    monkeypatch.setenv("CHECK_SIZE_MAX_FUNC", "1000")
    monkeypatch.setattr(sys, "argv", ["check_size.py", str(source)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
    assert capsys.readouterr().out == ""


def test_main_test_file_over_test_limit_flagged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    source = test_dir / "huge_test.py"
    source.write_text(_py_lines(1600), encoding="utf-8")
    monkeypatch.setenv("CHECK_SIZE_MAX_FILE", "800")
    monkeypatch.setenv("CHECK_SIZE_MAX_TEST_FILE", "1500")
    monkeypatch.setenv("CHECK_SIZE_MAX_FUNC", "1000")
    monkeypatch.setattr(sys, "argv", ["check_size.py", str(source)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "FILE_TOO_LONG" in capsys.readouterr().out


def test_main_non_test_file_uses_standard_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "big.py"
    source.write_text(_py_lines(900), encoding="utf-8")
    monkeypatch.setenv("CHECK_SIZE_MAX_FILE", "800")
    monkeypatch.setenv("CHECK_SIZE_MAX_TEST_FILE", "1500")
    monkeypatch.setenv("CHECK_SIZE_MAX_FUNC", "1000")
    monkeypatch.setattr(sys, "argv", ["check_size.py", str(source)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "FILE_TOO_LONG" in capsys.readouterr().out
