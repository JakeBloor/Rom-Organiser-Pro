"""
Step implementations for counting the games in a ROM library and finding new ones
"""

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import settings
from modules.cache import FileCache
from modules.library import pending_games, scan_library, system_folders


@pytest.fixture
def library_context(tmp_path):
    return {"root": tmp_path / "roms", "cache": FileCache(tmp_path / "cache" / "files.json")}


scenarios("../features/library.feature")


@given("a ROM library containing")
def rom_library(library_context, datatable):
    for (relative_path,) in datatable[1:]:
        path = library_context["root"] / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"data")


@given(parsers.parse('"{sheet}" points at "{track}"'))
def sheet_points_at(library_context, sheet, track):
    (library_context["root"] / sheet).write_text(f'FILE "{track}" BINARY\n')


@given("the ES-DE folder layout is chosen")
def esde_layout(monkeypatch):
    monkeypatch.setitem(settings.current, "multi_file_layout", "esde")


@when("the library is scanned")
def library_scanned(library_context):
    library_context["games"] = scan_library(library_context["root"])


@when(parsers.parse('the library is scanned for "{systems}"'))
def library_scanned_for(library_context, systems):
    library_context["games"] = scan_library(library_context["root"], systems.split(", "))


@given(parsers.parse('the app has organised "{paths}"'))
@when(parsers.parse('the app has organised "{paths}"'))
def app_has_organised(library_context, paths):
    for relative_path in paths.split(", "):
        library_context["cache"].remember(library_context["root"] / relative_path, outcome="organised")


@when(parsers.parse('"{relative_path}" is replaced'))
def file_replaced(library_context, relative_path):
    (library_context["root"] / relative_path).write_bytes(b"a different dump")


@when("new games are looked for")
def new_games_looked_for(library_context):
    library_context["pending"] = pending_games(library_context["root"], library_context["cache"])


@when("new games are looked for without a cache")
def new_games_looked_for_without_cache(library_context):
    library_context["pending"] = pending_games(library_context["root"])


@then("the games by system should be")
def games_by_system_are(library_context, datatable):
    expected = {system: int(games) for system, games in datatable[1:]}
    assert library_context["games"] == expected


@then(parsers.parse('the system folders should be "{systems}"'))
def system_folders_are(library_context, systems):
    assert system_folders(library_context["root"]) == systems.split(", ")


@then("the games waiting to be organised should be")
def games_waiting_are(library_context, datatable):
    root = library_context["root"]
    expected = {
        root / game: [root / track for track in tracks.split(", ") if track]
        for game, tracks in datatable[1:]
    }
    assert library_context["pending"] == expected


@then(parsers.parse('the games waiting to be organised should be "{games}"'))
def games_waiting_named(library_context, games):
    assert library_context["pending"] == {library_context["root"] / game: [] for game in games.split(", ")}
