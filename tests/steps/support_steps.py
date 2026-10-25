"""
Step implementations for ES-DE folders and app logging
"""

from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import esde, settings
from modules.logging_utils import AppLogger


@pytest.fixture
def support_context(tmp_path, monkeypatch):
    esde_home = tmp_path / "ES-DE"
    monkeypatch.setitem(settings.current, "esde_home", str(esde_home))
    monkeypatch.setitem(settings.current, "default_rom_folder", str(tmp_path / "Emulation" / "roms"))
    return {"esde_home": esde_home, "emudeck_root": tmp_path / "Emulation" / "roms"}


scenarios("../features/support.feature")


@given(
    parsers.parse(
        'ES-DE settings with ROMDirectory "{rom_dir}" and MediaDirectory "{media_dir}"'
    )
)
def esde_settings(support_context, rom_dir, media_dir):
    settings = support_context["esde_home"] / "settings" / "es_settings.xml"
    settings.parent.mkdir(parents=True)
    # ES-DE's settings file has no single root element, like the real one
    settings.write_text(
        '<?xml version="1.0"?>\n'
        '<bool name="ShowHiddenFiles" value="false" />\n'
        f'<string name="MediaDirectory" value="{media_dir}" />\n'
        f'<string name="ROMDirectory" value="{rom_dir}" />\n'
    )


@given("ES-DE settings with blank ROM and media folders")
def blank_esde_settings(support_context):
    esde_settings(support_context, "", "")


@given("ES-DE has no settings file")
def no_esde_settings():
    pass


@then(parsers.parse('the ROM folder should be "{rom_dir}" expanded'))
def rom_folder_expanded(rom_dir):
    assert esde.rom_root() == Path(rom_dir).expanduser()


@then(parsers.parse('the media folder should be "{media_dir}"'))
def media_folder_is(media_dir):
    assert esde.media_root() == Path(media_dir)


@then("the gamelists folder should be inside the ES-DE folder")
def gamelists_in_esde(support_context):
    assert esde.gamelists_root() == support_context["esde_home"] / "gamelists"


@then("the ROM folder should be the EmuDeck default")
def rom_folder_default(support_context):
    assert esde.rom_root() == support_context["emudeck_root"]


@then("the media folder should be inside the ES-DE folder")
def media_folder_default(support_context):
    assert esde.media_root() == support_context["esde_home"] / "downloaded_media"


@pytest.fixture
def log_context():
    return {}


@given("an app logger")
def app_logger(log_context):
    log_context["logger"] = AppLogger()


@given(parsers.parse("an app logger that keeps {count:d} messages"))
def app_logger_with_limit(log_context, count):
    log_context["logger"] = AppLogger()
    log_context["logger"].MAX_MESSAGES = count


@when(parsers.parse('"{message}" is logged at {level} level'))
def message_logged(log_context, message, level):
    logger = log_context["logger"]
    method = getattr(logger, level.lower(), None)
    if method:
        method(message)
    else:
        logger.log(message, level)


@when(parsers.parse("{count:d} messages are logged"))
def messages_logged(log_context, count):
    for number in range(1, count + 1):
        log_context["logger"].info(f"message {number}")


@then(parsers.parse('the logger should hold "{text}"'))
def logger_holds(log_context, text):
    assert log_context["logger"].get_messages() == [text]


@then(parsers.parse("the logger should hold messages {first:d} to {last:d}"))
def logger_holds_range(log_context, first, last):
    assert log_context["logger"].get_messages() == [
        f"ℹ️ message {number}" for number in range(first, last + 1)
    ]


@then("clearing the logger should empty it")
def clearing_empties(log_context):
    log_context["logger"].clear()
    assert log_context["logger"].get_messages() == []
