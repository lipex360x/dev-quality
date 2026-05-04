from __future__ import annotations

import sys
from pathlib import Path

import pytest
from check_noqa import check_file, main


def write_py(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.py"
    path.write_text(content, encoding="utf-8")
    return path


def test_flags_noqa_with_code(tmp_path: Path) -> None:
    path = write_py(tmp_path, "subprocess.run(['git'])  # noqa: S607\n")
    findings = check_file(path)
    assert len(findings) == 1
    assert "noqa" in findings[0]


def test_flags_noqa_bare(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # noqa\n")
    findings = check_file(path)
    assert len(findings) == 1


def test_flags_nosec_with_code(tmp_path: Path) -> None:
    path = write_py(tmp_path, "subprocess.run(cmd)  # nosec B603\n")
    findings = check_file(path)
    assert len(findings) == 1
    assert "nosec" in findings[0]


def test_flags_nosec_bare(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = dangerous()  # nosec\n")
    findings = check_file(path)
    assert len(findings) == 1


def test_passes_clean_file(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1\ny = 2\n")
    assert check_file(path) == []


def test_noqa_inside_string_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, 'content = "x = 1  # noqa: E501"\n')
    assert check_file(path) == []


def test_nosec_inside_string_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, 'doc = "use # nosec carefully"\n')
    assert check_file(path) == []


def test_finding_includes_file_and_line(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # noqa: E501\n")
    findings = check_file(path)
    assert str(path) in findings[0]
    assert ":1:" in findings[0]


def test_finding_includes_comment_text(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1  # noqa: E501\n")
    findings = check_file(path)
    assert "E501" in findings[0]


def test_multiple_violations_in_one_file(tmp_path: Path) -> None:
    path = write_py(
        tmp_path,
        "x = 1  # noqa: E501\ny = 2  # nosec B110\n",
    )
    assert len(check_file(path)) == 2


def test_main_exits_0_when_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = write_py(tmp_path, "x = 1\n")
    monkeypatch.setattr(sys, "argv", ["check-noqa", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_exits_1_when_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = write_py(tmp_path, "x = 1  # noqa: E501\n")
    monkeypatch.setattr(sys, "argv", ["check-noqa", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1


def test_main_prints_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = write_py(tmp_path, "x = 1  # noqa: E501\n")
    monkeypatch.setattr(sys, "argv", ["check-noqa", str(path)])
    with pytest.raises(SystemExit):
        main()
    assert "noqa" in capsys.readouterr().out


def test_main_multiple_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n", encoding="utf-8")
    dirty = tmp_path / "dirty.py"
    dirty.write_text("x = 1  # nosec B110\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check-noqa", str(clean), str(dirty)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1


def test_file_with_type_ignore_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x: int  # type: ignore\n")
    assert check_file(path) == []


def test_tokenize_error_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "broken.py"
    path.write_bytes(b"\xff\xfe invalid utf")
    assert check_file(path) == []


def test_tokenize_error_on_multiline_string_returns_empty(tmp_path: Path) -> None:
    path = write_py(tmp_path, '"""unterminated')
    assert check_file(path) == []
