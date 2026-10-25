"""
Step implementations for settings saved in settings.json
"""

import json
import stat
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import settings


@pytest.fixture
def settings_context():
    return {}


scenarios("../features/settings.feature")


def table_value(value):
    """Datatable cells are text: turn "true", "false", "none" and numbers into JSON values."""
    if value.isdigit():
        return int(value)
    return {"true": True, "false": False, "none": None}.get(value, value)


@given(parsers.parse('the SteamGridDB API key "{key}" is saved'))
def api_key_saved(key):
    assert settings.save({"steamgriddb_api": key}) == {}


def settings_file(name):
    return settings.SETTINGS_FILE if name == "settings.json" else settings.LOCAL_SETTINGS_FILE


@given(parsers.parse("{name} contains '{contents}'"))
def settings_file_contains(name, contents):
    settings_file(name).write_text(contents)


@given(parsers.parse('writing settings fails with "{message}"'))
def writing_fails(monkeypatch, message):
    def failing_replace(source, destination):
        raise OSError(message)

    monkeypatch.setattr("modules.settings.os.replace", failing_replace)


@when("the settings are saved with")
def settings_saved(settings_context, datatable):
    updates = {key: table_value(value) for key, value in datatable[1:]}
    try:
        settings_context["errors"] = settings.save(updates)
    except OSError as e:
        settings_context["raised"] = e


@when("the settings are loaded again")
def settings_loaded():
    settings.load()


@then(parsers.re(r'the "(?P<key>\w+)" setting should be (?P<number>\d+)$'))
def setting_is_number(key, number):
    assert settings.get(key) == int(number)


@then(parsers.parse('the "{key}" setting should be "{value}" expanded'))
def setting_is_expanded_path(key, value):
    assert settings.path(key) == Path(value).expanduser()


@then(parsers.re(r'the "(?P<key>\w+)" setting should be "(?P<value>[^"]*)"$'))
def setting_is_text(key, value):
    assert settings.get(key) == value


@then(parsers.parse('the "{key}" setting should be no folder'))
def setting_is_no_folder(key):
    assert settings.path(key) is None


@then(parsers.parse('the "{key}" setting should be off'))
def setting_is_off(key):
    assert settings.get(key) is False


@then("settings.local.json should be readable only by its owner")
def local_settings_file_private():
    assert stat.S_IMODE(settings.LOCAL_SETTINGS_FILE.stat().st_mode) == 0o600


@then(parsers.parse('settings.json should hold "{kept}" but not "{left_out}"'))
def settings_file_leaves_out(kept, left_out):
    stored = json.loads(settings.SETTINGS_FILE.read_text())
    assert kept in stored
    assert not set(left_out.split(", ")) & set(stored)


@then(parsers.parse('settings.local.json should hold only "{keys}"'))
def local_settings_file_holds(keys):
    assert sorted(json.loads(settings.LOCAL_SETTINGS_FILE.read_text())) == keys.split(", ")


@then(parsers.parse('saving should fail for "{key}" with "{message}"'))
def saving_fails(settings_context, key, message):
    assert message in settings_context["errors"][key]


@then("saving should succeed")
def saving_succeeds(settings_context):
    assert settings_context["errors"] == {}


@then("there should be no settings files")
def no_settings_files():
    assert not settings.SETTINGS_FILE.exists()
    assert not settings.LOCAL_SETTINGS_FILE.exists()


@then(parsers.parse('the page values should show the "{key}" secret as set'))
def secret_shown_as_set(key):
    assert settings.public_values()[key] is True


@then(parsers.parse('the settings should report "{problem}" for "{name}"'))
def settings_report(problem, name):
    assert problem in settings.load_error
    assert name in settings.load_error


@then(parsers.parse('saving should raise "{message}"'))
def saving_raises(settings_context, message):
    assert message in str(settings_context["raised"])


@then(parsers.parse('settings.local.json should still hold "{value}"'))
def local_settings_file_still_holds(value):
    assert json.loads(settings.LOCAL_SETTINGS_FILE.read_text())["steamgriddb_api"] == value
    assert settings.get("steamgriddb_api") == value


@then("no temporary settings files should be left")
def no_temporary_files():
    assert not list(settings.SETTINGS_FILE.parent.glob(".settings-*.json"))
