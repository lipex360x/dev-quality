from __future__ import annotations

import sys
from pathlib import Path

import pytest
from check_complexity import _check_bash, _line_score, _scan_file, main


def _bash(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / name
    script.write_text(
        f"#!/usr/bin/env bash\nset -euo pipefail\n\nfunc() {{\n{body}\n}}\n",
        encoding="utf-8",
    )
    return script


def test_line_score_comment_is_zero() -> None:
    assert _line_score("    # comment") == 0


def test_line_score_if_is_one() -> None:
    assert _line_score("    if true; then") == 1


def test_line_score_elif_is_one() -> None:
    assert _line_score("    elif false; then") == 1


def test_line_score_for_is_one() -> None:
    assert _line_score("    for i in 1; do") == 1


def test_line_score_while_is_one() -> None:
    assert _line_score("    while true; do") == 1


def test_line_score_until_is_one() -> None:
    assert _line_score("    until false; do") == 1


def test_line_score_case_branch() -> None:
    assert _line_score("    a) echo a ;;") == 1


def test_line_score_plain_line_is_zero() -> None:
    assert _line_score("    echo hi") == 0


def test_no_files_exits_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_complexity.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_python_files_skipped(tmp_path: Path) -> None:
    source = tmp_path / "script.py"
    source.write_text(
        "def foo():\n    if a:\n        if b:\n            if c:\n                pass\n",
        encoding="utf-8",
    )
    assert _scan_file(source, 3) == []


def test_clean_function_at_threshold(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "clean.sh",
        "    if true; then\n        for i in 1 2; do\n            while false; do\n"
        "                echo hi\n            done\n        done\n    fi",
    )
    assert _check_bash(script, 4) == []


def test_flagged_over_threshold(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    if true; then\n        for i in 1 2; do\n            while false; do\n"
        "                until false; do\n                    elif true; then\n"
        "                        echo hi\n                    fi\n"
        "                done\n            done\n        done\n    fi",
    )
    findings = _check_bash(script, 3)
    assert len(findings) == 1
    assert "COMPLEXITY" in findings[0]


def test_if_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    if true; then\n"
        "                        echo hi\n                    fi\n                fi\n"
        "            fi\n        fi\n    fi",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_elif_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    if true; then\n        echo a\n    elif false; then\n        echo b\n"
        "    elif false; then\n        echo c\n    elif false; then\n        echo d\n"
        "    elif false; then\n        echo e\n    fi",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_for_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    for a in 1; do\n        for b in 2; do\n            for c in 3; do\n"
        "                for d in 4; do\n                    echo hi\n"
        "                done\n            done\n        done\n    done",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_while_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    while true; do\n        while true; do\n            while true; do\n"
        "                while true; do\n                    break\n"
        "                done\n            done\n        done\n    done",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_until_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        "    until false; do\n        until false; do\n            until false; do\n"
        "                until false; do\n                    break\n"
        "                done\n            done\n        done\n    done",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_case_branch_increments_complexity(tmp_path: Path) -> None:
    script = _bash(
        tmp_path,
        "bad.sh",
        '    case "$x" in\n        a) echo a ;;\n        b) echo b ;;\n'
        "        c) echo c ;;\n        d) echo d ;;\n        e) echo e ;;\n    esac",
    )
    findings = _check_bash(script, 3)
    assert any("COMPLEXITY" in f for f in findings)


def test_reports_function_name(tmp_path: Path) -> None:
    script = tmp_path / "named.sh"
    script.write_text(
        "#!/usr/bin/env bash\nmy_func() {\n"
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    if true; then\n"
        "                        echo hi\n                    fi\n                fi\n"
        "            fi\n        fi\n    fi\n}\n",
        encoding="utf-8",
    )
    findings = _check_bash(script, 3)
    assert any("my_func" in f for f in findings)


def test_reports_line_number(tmp_path: Path) -> None:
    script = tmp_path / "lined.sh"
    script.write_text(
        "#!/usr/bin/env bash\nmy_func() {\n"
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    echo hi\n"
        "                fi\n            fi\n        fi\n    fi\n}\n",
        encoding="utf-8",
    )
    findings = _check_bash(script, 3)
    assert any(":2:" in f for f in findings)


def test_multiple_functions_checked_independently(tmp_path: Path) -> None:
    script = tmp_path / "multi.sh"
    script.write_text(
        "#!/usr/bin/env bash\nclean_func() {\n    echo hi\n}\n"
        "complex_func() {\n"
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    if true; then\n"
        "                        echo hi\n                    fi\n                fi\n"
        "            fi\n        fi\n    fi\n}\n",
        encoding="utf-8",
    )
    findings = _check_bash(script, 3)
    assert any("complex_func" in f for f in findings)
    assert not any("clean_func" in f for f in findings)


def test_read_error_returns_error_token(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sh"
    findings = _check_bash(missing, 3)
    assert len(findings) == 1
    assert findings[0].startswith("READ_ERROR:")


def test_token_format(tmp_path: Path) -> None:
    script = tmp_path / "fmt.sh"
    script.write_text(
        "#!/usr/bin/env bash\nmy_func() {\n"
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    echo hi\n"
        "                fi\n            fi\n        fi\n    fi\n}\n",
        encoding="utf-8",
    )
    findings = _check_bash(script, 3)
    assert findings[0].startswith("COMPLEXITY:")


def test_main_dirty_exits_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script = tmp_path / "bad.sh"
    script.write_text(
        "#!/usr/bin/env bash\nmy_func() {\n"
        "    if true; then\n        if true; then\n            if true; then\n"
        "                if true; then\n                    echo hi\n"
        "                fi\n            fi\n        fi\n    fi\n}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHECK_COMPLEXITY_MAX", "3")
    monkeypatch.setattr(sys, "argv", ["check_complexity.py", str(script)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "COMPLEXITY" in capsys.readouterr().out


def test_main_clean_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = tmp_path / "ok.sh"
    script.write_text("#!/usr/bin/env bash\nfunc() {\n    echo hi\n}\n", encoding="utf-8")
    monkeypatch.setenv("CHECK_COMPLEXITY_MAX", "3")
    monkeypatch.setattr(sys, "argv", ["check_complexity.py", str(script)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_single_line_function_skipped(tmp_path: Path) -> None:
    script = tmp_path / "oneliner.sh"
    script.write_text(
        "#!/usr/bin/env bash\nsingle_func() { echo hi; }\n",
        encoding="utf-8",
    )
    assert _check_bash(script, 3) == []
