"""Smoke tests: package import and settings."""

import os
from pathlib import Path

import pytest

from ai_security_camera import __version__
from ai_security_camera.config import Settings


def test_version_is_semantic() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts[:2])


@pytest.fixture
def isolated_settings_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for key in list(os.environ):
        if key.startswith("ASC_"):
            monkeypatch.delenv(key, raising=False)


def test_settings_defaults(isolated_settings_env: None) -> None:
    s = Settings()
    assert s.api_port == 8000
    assert "sqlite" in s.database_url
