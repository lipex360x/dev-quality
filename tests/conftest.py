from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
import yaml


@pytest.fixture(autouse=True)
def _patch_user_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("check_all._user_cache_dir", lambda: tmp_path / "cache")


def _make_files(tmp_path: Path, names: list[str]) -> list[Path]:
    files = []
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        files.append(path)
    return files


def _write_config(tmp_path: Path, data: dict[str, object]) -> None:
    (tmp_path / ".dev-quality.yaml").write_text(yaml.dump(data), encoding="utf-8")


def _stub_collect(
    tmp_path: Path,
    python_names: Sequence[str] = (),
    shell_names: Sequence[str] = (),
) -> Callable[[Path, frozenset[str]], list[Path]]:
    py_files = [tmp_path / name for name in python_names]
    sh_files = [tmp_path / name for name in shell_names]

    def impl(root: Path, suffixes: frozenset[str]) -> list[Path]:
        if ".py" in suffixes:
            return list(py_files)
        return list(sh_files)

    return impl
