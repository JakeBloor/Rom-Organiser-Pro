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
