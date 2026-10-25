import sys
from pathlib import Path

import pytest

# Add parent directory to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_app_logger():
    from app import app_logger

    app_logger.clear()
    yield
    app_logger.clear()


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Every test starts from the default settings and an empty file cache, never the real ones, and never sees ES-DE."""
    from modules import settings

    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(settings, "LOCAL_SETTINGS_FILE", tmp_path / "settings.local.json")
    settings.load()
    monkeypatch.setitem(settings.current, "esde_home", str(tmp_path / "no-ES-DE"))

    import app
    from modules.cache import FileCache

    monkeypatch.setattr(app, "file_cache", FileCache(tmp_path / "cache" / "files.json"))
    app.new_roms.update(rom_root=None, new=[], needs_attention=[], checked=None)
    yield

    # A run left going in its worker thread must finish before the real cache comes back
    assert app.organise_lock.acquire(timeout=10), "an organise run did not finish"
    app.organise_lock.release()
    settings.load()
