import pytest

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
