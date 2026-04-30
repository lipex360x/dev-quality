from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from check_comments import check_bash_file, check_python_file, main


def write_py(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.py"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def write_sh(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.sh"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_py_clean_returns_empty(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1\ny = 2\n")
    assert check_python_file(path) == []


def test_py_block_comment_detected(tmp_path: Path) -> None:
    path = write_py(tmp_path, "# this is a comment\nx = 1\n")
    findings = check_python_file(path)
    assert len(findings) == 1
    assert findings[0].startswith(f"COMMENT:{path}:1:")


def test_py_inline_comment_detected(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # inline comment\n")
    findings = check_python_file(path)
    assert len(findings) == 1
    assert findings[0].startswith(f"COMMENT:{path}:1:")


def test_py_type_ignore_allowed(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # type: ignore\n")
    assert check_python_file(path) == []


def test_py_noqa_allowed(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # noqa\n")
    assert check_python_file(path) == []


def test_py_noqa_with_code_allowed(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # noqa: E501\n")
    assert check_python_file(path) == []


def test_py_pyright_ignore_allowed(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # pyright: ignore\n")
    assert check_python_file(path) == []


def test_py_multiple_comments_all_detected(tmp_path: Path) -> None:
    path = write_py(tmp_path, "# first\nx = 1  # second\ny = 2\n")
    findings = check_python_file(path)
    assert len(findings) == 2


def test_py_parse_error_returns_error_token(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_bytes(b"\xff\xfe invalid utf8 \x00")
    findings = check_python_file(path)
    assert len(findings) == 1
    assert findings[0].startswith("PARSE_ERROR:")


def test_bash_clean_returns_empty(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "x=1\ny=2\n")
    assert check_bash_file(path) == []


def test_bash_block_comment_detected(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "#!/usr/bin/env bash\n# block comment\nx=1\n")
    findings = check_bash_file(path)
    assert len(findings) == 1
    assert findings[0].startswith(f"COMMENT:{path}:2:")


def test_bash_shebang_allowed(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "#!/usr/bin/env bash\nx=1\n")
    assert check_bash_file(path) == []


def test_bash_shellcheck_directive_allowed(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "# shellcheck disable=SC2034\nx=1\n")
    assert check_bash_file(path) == []


def test_bash_shellcheck_source_allowed(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "# shellcheck source=lib/log.sh\nx=1\n")
    assert check_bash_file(path) == []


def test_bash_multiple_comments_all_detected(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "#!/usr/bin/env bash\n# first\n# second\nx=1\n")
    findings = check_bash_file(path)
    assert len(findings) == 2


def test_bash_read_error_returns_error_token(tmp_path: Path) -> None:
    path = tmp_path / "missing.sh"
    findings = check_bash_file(path)
    assert len(findings) == 1
    assert findings[0].startswith("PARSE_ERROR:")


def test_bash_section_separator_detected(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "#!/usr/bin/env bash\n# --- Section ---\nx=1\n")
    findings = check_bash_file(path)
    assert len(findings) == 1
    assert "Section" in findings[0]


def test_main_no_args_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_comments.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_clean_py_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_py(tmp_path, "x = 1\n")
    monkeypatch.setattr(sys, "argv", ["check_comments.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_dirty_py_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_py(tmp_path, "# bad comment\nx = 1\n")
    monkeypatch.setattr(sys, "argv", ["check_comments.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "COMMENT:" in capsys.readouterr().out


def test_main_dispatches_bash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_sh(tmp_path, "#!/usr/bin/env bash\n# comment\nx=1\n")
    monkeypatch.setattr(sys, "argv", ["check_comments.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
