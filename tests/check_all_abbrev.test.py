from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from check_all import main
from conftest import _stub_collect, _write_config


def test_main_passes_abbrev_min_length_to_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"abbrev_min_length": 3})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, python_names=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    abbrev_calls = [call for call in mock_run.call_args_list if call[0][0][0] == "check-abbrev"]
    assert abbrev_calls
    env_passed = abbrev_calls[0][1].get("env", {})
    assert env_passed.get("CHECK_ABBREV_MIN_LENGTH") == "3"


def test_main_passes_abbrev_allowlist_extra_to_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, {"abbrev_allowlist": ["py", "sh"]})
    monkeypatch.setattr(sys, "argv", ["check-all", str(tmp_path)])
    ok = MagicMock(returncode=0, stdout="", stderr="")
    with (
        patch("check_all._collect", side_effect=_stub_collect(tmp_path, python_names=["ok.py"])),
        patch("subprocess.run", return_value=ok) as mock_run,
        pytest.raises(SystemExit),
    ):
        main()
    abbrev_calls = [call for call in mock_run.call_args_list if call[0][0][0] == "check-abbrev"]
    assert abbrev_calls
    env_passed = abbrev_calls[0][1].get("env", {})
    assert env_passed.get("CHECK_ABBREV_ALLOWLIST_EXTRA") == "py,sh"
