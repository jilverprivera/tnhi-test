"""Configuration lives only in the environment: unset means undefined, never a value from code."""

import pytest

from app.container import Container
from app.shared.config import API_ROOT, MissingSettingError, Settings


def test_unset_settings_are_undefined(monkeypatch):
    for name in ("TAC_TODAY", "TAC_CLERK_TOKEN", "TAC_LLM_MODEL", "TAC_WORKER_ENABLED"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.today is None and settings.clerk_token is None
    assert settings.llm_model is None and settings.worker_enabled is None
    assert not settings.assisted_classification_ready()


def test_a_required_setting_fails_loudly():
    container = Container(Settings(_env_file=None))
    with pytest.raises(MissingSettingError, match="TAC_DATA_DIR is not set"):
        _ = container.sessions


def test_relative_paths_resolve_against_the_api_folder():
    settings = Settings(_env_file=None, data_dir="data", database_url="sqlite:///data/tac.db")
    assert settings.data_dir == (API_ROOT / "data").resolve()
    assert settings.database_url == f"sqlite:///{(API_ROOT / 'data' / 'tac.db').resolve()}"
