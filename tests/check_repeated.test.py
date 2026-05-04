from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
from check_repeated import check_file, main

_LONG_LINE = 'gitignore = project / ".gitignore"'


def write_py(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.py"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def write_sh(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.sh"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_py_repeated_line_flagged(tmp_path: Path) -> None:
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    findings = check_file(path)
    assert len(findings) == 1
    assert findings[0].startswith(f"REPEATED:{path}:")


def test_sh_repeated_line_flagged(tmp_path: Path) -> None:
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_sh(tmp_path, content)
    findings = check_file(path)
    assert len(findings) == 1
    assert findings[0].startswith(f"REPEATED:{path}:")


def test_output_format(tmp_path: Path) -> None:
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    findings = check_file(path)
    assert findings == [f"REPEATED:{path}:1,2,3:{_LONG_LINE}"]


def test_at_threshold_not_flagged(tmp_path: Path) -> None:
    content = "\n".join([_LONG_LINE] * 2) + "\n"
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_above_threshold_flagged(tmp_path: Path) -> None:
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_closing_bracket_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, ")\n" * 50)
    assert check_file(path) == []


def test_pass_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "pass\n" * 5)
    assert check_file(path) == []


def test_continue_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "continue\n" * 5)
    assert check_file(path) == []


def test_break_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "break\n" * 5)
    assert check_file(path) == []


def test_return_none_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "return None\n" * 5)
    assert check_file(path) == []


def test_return_true_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "return True\n" * 5)
    assert check_file(path) == []


def test_return_false_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "return False\n" * 5)
    assert check_file(path) == []


def test_bare_return_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "return\n" * 5)
    assert check_file(path) == []


def test_else_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "else:\n" * 5)
    assert check_file(path) == []


def test_try_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "try:\n" * 5)
    assert check_file(path) == []


def test_finally_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "finally:\n" * 5)
    assert check_file(path) == []


def test_except_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "except Exception as error:\n" * 5)
    assert check_file(path) == []


def test_bash_done_not_flagged(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "done\n" * 5)
    assert check_file(path) == []


def test_bash_fi_not_flagged(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "fi\n" * 5)
    assert check_file(path) == []


def test_bash_esac_not_flagged(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "esac\n" * 5)
    assert check_file(path) == []


def test_bash_closing_brace_not_flagged(tmp_path: Path) -> None:
    path = write_sh(tmp_path, "}\n" * 5)
    assert check_file(path) == []


def test_short_line_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "x = 1\n" * 5)
    assert check_file(path) == []


def test_decorator_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "@pytest.fixture\n" * 5)
    assert check_file(path) == []


def test_comment_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "# something something something something\n" * 5)
    assert check_file(path) == []


def test_empty_lines_not_flagged(tmp_path: Path) -> None:
    path = write_py(tmp_path, "\n" * 50)
    assert check_file(path) == []


def test_docstring_lines_not_flagged(tmp_path: Path) -> None:
    content = '"""\n' + (_LONG_LINE + "\n") * 3 + '"""\n'
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_single_quote_docstring_not_flagged(tmp_path: Path) -> None:
    content = "'''\n" + (_LONG_LINE + "\n") * 3 + "'''\n"
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_single_line_docstring_marked(tmp_path: Path) -> None:
    line = '"""' + _LONG_LINE + '"""'
    content = (line + "\n") * 3
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_docstring_skipped_for_sh_files(tmp_path: Path) -> None:
    content = '"""\n' + (_LONG_LINE + "\n") * 3 + '"""\n'
    path = write_sh(tmp_path, content)
    findings = check_file(path)
    assert len(findings) == 1


def test_multiple_distinct_repeated_lines(tmp_path: Path) -> None:
    line_a = 'gitignore = project / ".gitignore"'
    line_b = 'editorconfig = project / ".editorconfig"'
    content = "\n".join([line_a] * 3 + [line_b] * 3) + "\n"
    path = write_py(tmp_path, content)
    findings = check_file(path)
    assert len(findings) == 2


def test_max_repetitions_env_allows_three(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_REPEATED_MAX_REPETITIONS", "3")
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_max_repetitions_env_fails_on_four(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_REPEATED_MAX_REPETITIONS", "3")
    content = "\n".join([_LONG_LINE] * 4) + "\n"
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_min_line_length_env_filters_short(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_REPEATED_MIN_LINE_LENGTH", "30")
    short_line = 'path = root / "data"'
    content = "\n".join([short_line] * 3) + "\n"
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_min_line_length_env_flags_long(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_REPEATED_MIN_LINE_LENGTH", "30")
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_parse_error_returns_error_token(tmp_path: Path) -> None:
    path = tmp_path / "missing.py"
    findings = check_file(path)
    assert len(findings) == 1
    assert findings[0].startswith("PARSE_ERROR:")


def test_smoke_setup_py(tmp_path: Path) -> None:
    content = textwrap.dedent("""\
        from pathlib import Path

        project = Path(__file__).parent

        def setup_gitignore() -> None:
            gitignore = project / ".gitignore"
            gitignore.write_text("__pycache__\\n")

        def setup_editorconfig() -> None:
            gitignore = project / ".gitignore"
            gitignore.unlink(missing_ok=True)

        def setup_readme() -> None:
            gitignore = project / ".gitignore"
            gitignore.touch()
    """)
    path = write_py(tmp_path, content)
    findings = check_file(path)
    assert len(findings) == 1
    assert 'gitignore = project / ".gitignore"' in findings[0]


def test_function_call_rhs_not_flagged(tmp_path: Path) -> None:
    line = "config_path = load_config_file(default_path, encoding)"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_constructor_rhs_not_flagged(tmp_path: Path) -> None:
    line = "mock_response = MagicMock(returncode=0, stdout='')"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_subscript_rhs_not_flagged(tmp_path: Path) -> None:
    line = "config_value = settings_dictionary['some_key']"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_list_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "expected_items = [1, 2, 3, 4, 5, 6, 7]"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_dict_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "headers_map = {'Content-Type': 'application/json'}"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_typed_assignment_not_flagged(tmp_path: Path) -> None:
    line = "counter_total: int = 42 * 100 * 7"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_assert_statement_not_flagged(tmp_path: Path) -> None:
    line = "assert process_input(value) == expected_result"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_function_param_with_comma_not_flagged(tmp_path: Path) -> None:
    line = "default_argument = SOME_LONG_CONSTANT_NAME,"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_attribute_chain_assignment_flagged(tmp_path: Path) -> None:
    line = "database_url = settings.database.connection_url"
    content = (line + "\n") * 3
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_arithmetic_assignment_flagged(tmp_path: Path) -> None:
    line = "total_seconds = base_seconds + extra_offset"
    content = (line + "\n") * 3
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_string_literal_assignment_flagged(tmp_path: Path) -> None:
    line = 'API_PREFIX = "https://api.example.com/v1"'
    content = (line + "\n") * 3
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_method_chain_not_flagged(tmp_path: Path) -> None:
    line = "result_text = base_string.strip().lower()"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_function_signature_not_flagged(tmp_path: Path) -> None:
    line = "def setup_helper_function() -> None:"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_false_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "block_has_references_marker = False"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_true_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "block_has_references_marker = True"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_none_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "current_state_marker_value = None"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_integer_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "current_iteration_counter = 0"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_negative_integer_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "current_signed_offset_value = -1"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_float_literal_rhs_not_flagged(tmp_path: Path) -> None:
    line = "current_ratio_threshold = 0.75"
    content = (line + "\n") * 5
    path = write_py(tmp_path, content)
    assert check_file(path) == []


def test_string_literal_still_flagged(tmp_path: Path) -> None:
    line = 'shared_api_prefix = "https://api.example.com/v1"'
    content = (line + "\n") * 3
    path = write_py(tmp_path, content)
    assert len(check_file(path)) == 1


def test_main_no_args_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_repeated.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_clean_file_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_py(tmp_path, "x = 1\n")
    monkeypatch.setattr(sys, "argv", ["check_repeated.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_repeated_exits_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    content = "\n".join([_LONG_LINE] * 3) + "\n"
    path = write_py(tmp_path, content)
    monkeypatch.setattr(sys, "argv", ["check_repeated.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "REPEATED:" in capsys.readouterr().out
