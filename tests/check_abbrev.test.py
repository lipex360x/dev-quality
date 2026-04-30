from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from check_abbrev import (
    _check_bash_file,
    _check_file,
    _load_rules,
    _scan_file,
    main,
)

_DENY: frozenset[str] = frozenset(["ext", "cfg", "ref", "buf", "err", "exc", "fmt", "dest"])
_ALLOW: frozenset[str] = frozenset(["self", "cls", "args", "kwargs", "i", "j", "k", "_", "id", "ok"])
_LANG: dict[str, frozenset[str]] = {"sh": frozenset(["dest"])}


def _py(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.py"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _sh(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.sh"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_clean_variable(tmp_path: Path) -> None:
    path = _py(tmp_path, "extension = 'py'\n")
    assert _check_file(path, _DENY, _ALLOW) == []


def test_clean_param(tmp_path: Path) -> None:
    path = _py(tmp_path, "def process(extension: str) -> bool:\n    return True\n")
    assert _check_file(path, _DENY, _ALLOW) == []


def test_allows_self_and_cls(tmp_path: Path) -> None:
    path = _py(
        tmp_path,
        "class Foo:\n"
        "    def method(self) -> None:\n"
        "        pass\n"
        "    @classmethod\n"
        "    def create(cls) -> 'Foo':\n"
        "        return cls()\n",
    )
    assert _check_file(path, _DENY, _ALLOW) == []


def test_allows_args_kwargs(tmp_path: Path) -> None:
    path = _py(tmp_path, "def process(*args: object, **kwargs: object) -> None:\n    pass\n")
    assert _check_file(path, _DENY, _ALLOW) == []


def test_detects_ext_variable(tmp_path: Path) -> None:
    path = _py(tmp_path, "ext = 'py'\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert len(findings) == 1
    assert "ABBREV" in findings[0]
    assert "ext" in findings[0]


def test_detects_ref_variable(tmp_path: Path) -> None:
    path = _py(tmp_path, "ref = get_ref()\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("ref" in f for f in findings)


def test_detects_cfg_variable(tmp_path: Path) -> None:
    path = _py(tmp_path, "cfg = load_config()\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("cfg" in f for f in findings)


def test_detects_abbreviation_in_function_param(tmp_path: Path) -> None:
    path = _py(tmp_path, "def process(ext: str) -> None:\n    pass\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("ext" in f for f in findings)


def test_detects_abbreviation_in_for_loop(tmp_path: Path) -> None:
    path = _py(tmp_path, "for ext in extensions:\n    pass\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("ext" in f for f in findings)


def test_walrus_not_flagged(tmp_path: Path) -> None:
    path = _py(tmp_path, "import re\nif mat := re.match(r'x', 'x'):\n    pass\n")
    assert _check_file(path, _DENY, _ALLOW) == []


def test_detects_abbreviation_in_except_handler(tmp_path: Path) -> None:
    path = _py(tmp_path, "try:\n    pass\nexcept Exception as exc:\n    pass\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("exc" in f for f in findings)


def test_detects_abbreviation_in_with_statement(tmp_path: Path) -> None:
    path = _py(tmp_path, "with open('f') as buf:\n    pass\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("buf" in f for f in findings)


def test_reports_line_number(tmp_path: Path) -> None:
    path = _py(tmp_path, "x = 1\next = 'py'\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any(":2:" in f for f in findings)


def test_multiple_findings_in_one_file(tmp_path: Path) -> None:
    path = _py(tmp_path, "ext = 'py'\nref = get_ref()\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert len(findings) == 2


def test_parse_error_returns_error_token(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_bytes(b"\xff\xfe invalid utf8")
    findings = _check_file(path, _DENY, _ALLOW)
    assert len(findings) == 1
    assert findings[0].startswith("PARSE_ERROR:")


def test_bash_clean_variable(tmp_path: Path) -> None:
    path = _sh(tmp_path, "extension='py'\n")
    assert _check_bash_file(path, _DENY, _ALLOW) == []


def test_bash_detects_local_abbrev(tmp_path: Path) -> None:
    path = _sh(tmp_path, "local ext='py'\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("ext" in f for f in findings)


def test_bash_detects_plain_assignment(tmp_path: Path) -> None:
    path = _sh(tmp_path, "cfg=load_config\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("cfg" in f for f in findings)


def test_bash_detects_readonly(tmp_path: Path) -> None:
    path = _sh(tmp_path, "readonly ref='value'\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("ref" in f for f in findings)


def test_bash_detects_declare(tmp_path: Path) -> None:
    path = _sh(tmp_path, "declare -r buf='value'\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("buf" in f for f in findings)


def test_bash_detects_for_loop_var(tmp_path: Path) -> None:
    path = _sh(tmp_path, 'for ext in *.py; do echo "$ext"; done\n')
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("ext" in f for f in findings)


def test_bash_allows_loop_index_vars(tmp_path: Path) -> None:
    path = _sh(tmp_path, 'for i in 1 2 3; do echo "$i"; done\n')
    assert _check_bash_file(path, _DENY, _ALLOW) == []


def test_bash_detects_function_abbrev(tmp_path: Path) -> None:
    path = _sh(tmp_path, "function fmt() { echo 'hi'; }\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("fmt" in f for f in findings)


def test_bash_detects_function_posix_style(tmp_path: Path) -> None:
    path = _sh(tmp_path, "cfg() { echo 'config'; }\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any("cfg" in f for f in findings)


def test_bash_clean_function_name(tmp_path: Path) -> None:
    path = _sh(tmp_path, "function format_output() { echo 'hi'; }\n")
    assert _check_bash_file(path, _DENY, _ALLOW) == []


def test_bash_reports_line_number(tmp_path: Path) -> None:
    path = _sh(tmp_path, "#!/usr/bin/env bash\nlocal ext='py'\n")
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert any(":2:" in f for f in findings)


def test_bash_read_error_returns_error_token(tmp_path: Path) -> None:
    path = tmp_path / "missing.sh"
    findings = _check_bash_file(path, _DENY, _ALLOW)
    assert len(findings) == 1
    assert findings[0].startswith("PARSE_ERROR:")


def test_bash_allowlist_sh_passes_in_sh(tmp_path: Path) -> None:
    path = _sh(tmp_path, "local dest='value'\n")
    assert _check_bash_file(path, _DENY, _ALLOW, _LANG) == []


def test_bash_allowlist_sh_flagged_in_py(tmp_path: Path) -> None:
    path = _py(tmp_path, "dest = 'value'\n")
    findings = _check_file(path, _DENY, _ALLOW)
    assert any("dest" in f for f in findings)


def test_scan_file_dispatches_sh(tmp_path: Path) -> None:
    path = _sh(tmp_path, "cfg=x\n")
    findings = _scan_file(path, _DENY, _ALLOW, _LANG)
    assert any("cfg" in f for f in findings)


def test_scan_file_dispatches_py(tmp_path: Path) -> None:
    path = _py(tmp_path, "ext = 'py'\n")
    findings = _scan_file(path, _DENY, _ALLOW, _LANG)
    assert any("ext" in f for f in findings)


def test_load_rules_returns_frozensets(tmp_path: Path) -> None:
    rules_file = tmp_path / "abbrev.yaml"
    rules_file.write_text(
        yaml.dump({"denylist": ["ext"], "allowlist": ["self"], "allowlist_sh": ["dest"]}),
        encoding="utf-8",
    )
    deny, allow, lang = _load_rules(rules_file)
    assert "ext" in deny
    assert "self" in allow
    assert "dest" in lang.get("sh", frozenset())


def test_load_rules_uses_defaults_when_path_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such.yaml"
    deny, allow, lang = _load_rules(missing)
    assert len(deny) > 0
    assert "self" in allow


def test_main_no_args_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_abbrev.py"])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_clean_file_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _py(tmp_path, "extension = 'py'\n")
    monkeypatch.setattr(sys, "argv", ["check_abbrev.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0


def test_main_dirty_file_exits_1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _py(tmp_path, "ext = 'py'\n")
    monkeypatch.setattr(sys, "argv", ["check_abbrev.py", str(path)])
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 1
    assert "ABBREV" in capsys.readouterr().out
