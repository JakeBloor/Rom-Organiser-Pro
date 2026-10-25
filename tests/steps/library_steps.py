"""
Step implementations for counting the games in a ROM library
"""

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules.library import scan_library, system_folders


@pytest.fixture
def library_context(tmp_path):
    return {"root": tmp_path / "roms"}


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


@when("the library is scanned")
def library_scanned(library_context):
    library_context["games"], library_context["undetected"] = scan_library(
        library_context["root"]
    )


@when(parsers.parse('the library is scanned for "{systems}"'))
def library_scanned_for(library_context, systems):
    library_context["games"], library_context["undetected"] = scan_library(
        library_context["root"], systems.split(", ")
    )


@then("the games by system should be")
def games_by_system_are(library_context, datatable):
    expected = {system: int(games) for system, games in datatable[1:]}
    assert library_context["games"] == expected


@then(parsers.parse('the undetected files should be "{names}"'))
def undetected_files_are(library_context, names):
    assert library_context["undetected"] == names.split(", ")


@then("there should be no undetected files")
def no_undetected_files(library_context):
    assert library_context["undetected"] == []


@then(parsers.parse('the system folders should be "{systems}"'))
def system_folders_are(library_context, systems):
    assert system_folders(library_context["root"]) == systems.split(", ")
