import pytest

from pytest_bdd import given, scenario, then, when

from app import app as flask_app, initialize_dat_files
from modules.dat_validation import DAT_DB, load_dat_files, validate_hashes
import app as rom_app


@scenario("features/app.feature", "Main page loads")
def test_main_page_loads():
    pass


@scenario("features/app.feature", "Logs page loads")
def test_logs_page_loads():
    pass


@scenario("features/app.feature", "DAT validation loads sample DAT entries")
def test_dat_validation_loads_sample_entries():
    pass


@scenario("features/app.feature", "DAT auto-download runs on startup")
def test_dat_auto_download_runs_on_startup():
    pass


@given("the Flask application is configured for testing")
def flask_application_configured_for_testing(client):
    return client


@when("the homepage is requested")
def homepage_requested(client, context):
    context["response"] = client.get("/")
    return context["response"]


@when("the logs page is requested")
def logs_page_requested(client, context):
    context["response"] = client.get("/logs")
    return context["response"]


@then("the response status code should be 200")
def response_should_be_ok(context):
    assert context["response"].status_code == 200


@then('the homepage should contain "ROM Organizer Pro"')
def homepage_contains_title(context):
    assert b"ROM Organizer Pro" in context["response"].data


@then('the logs page should contain "Log Viewer"')
def logs_page_contains_title(context):
    assert b"Log Viewer" in context["response"].data


@pytest.fixture
def sample_dat_directory(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.dat_validation.DAT_DIR", tmp_path)

    sample_dat = tmp_path / "sample.dat"
    sample_dat.write_text("""<?xml version=\"1.0\"?>
<datafile>
  <game name=\"Super Mario Bros.\">
    <rom name=\"Super Mario Bros.nes\" size=\"40976\" crc=\"3337ec46\" md5=\"d60e3d1a9d2f2ff1a1141df7fda6e693\" sha1=\"99b09c05df1b6f6ef9b49c0adf5bbffc1c7e0d60\" />
  </game>
</datafile>
""")
    return tmp_path


@given("a temporary DAT directory and file exist")
def temporary_dat_directory_and_file_exist(sample_dat_directory):
    return sample_dat_directory


@when("the DAT files are loaded")
def dat_files_are_loaded(sample_dat_directory):
    DAT_DB.clear()
    load_dat_files(lambda message, level="INFO": None)


@then('the hash lookup should return "Super Mario Bros." for the sample MD5')
def hash_lookup_returns_sample_game():
    result = validate_hashes({"md5": "d60e3d1a9d2f2ff1a1141df7fda6e693"})
    assert result == "Super Mario Bros."


@pytest.fixture
def dat_fetch_and_load_stubs(monkeypatch):
    called = {}

    def fake_fetch(logger):
        called["fetch"] = True
        return {}

    def fake_load(logger):
        called["load"] = True

    monkeypatch.setattr(rom_app, "fetch_latest_dats", fake_fetch)
    monkeypatch.setattr(rom_app, "load_dat_files", fake_load)
    return called


@given("DAT fetch and load functions are stubbed")
def dat_fetch_and_load_functions_are_stubbed(dat_fetch_and_load_stubs):
    return dat_fetch_and_load_stubs


@when("initialize_dat_files is called")
def initialize_dat_files_called():
    initialize_dat_files()


@then("the DAT fetch function should be invoked")
def dat_fetch_function_should_be_invoked(dat_fetch_and_load_stubs):
    assert dat_fetch_and_load_stubs.get("fetch", False)


@then("the DAT load function should also be invoked")
def dat_load_function_should_be_invoked(dat_fetch_and_load_stubs):
    assert dat_fetch_and_load_stubs.get("load", False)


@pytest.fixture
def context():
    return {}
