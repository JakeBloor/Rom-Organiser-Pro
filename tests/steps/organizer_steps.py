"""
Step implementations for ROM organiser tests
"""

import hashlib
import zipfile

import pytest
from pytest_bdd import given, scenario, scenarios, then, when, parsers

from modules import settings

from modules.dat_validation import DAT_DB
from modules.organizer import process_roms

EXISTING_ROM_CONTENT = b"existing rom"
GAMECUBE_MAGIC_OFFSET = 0x1C
GAMECUBE_MAGIC = bytes.fromhex("C2339F3D")


@pytest.fixture
def organiser_context(tmp_path, monkeypatch):
    rom_root = tmp_path / "roms"
    rom_root.mkdir()
    import_dir = tmp_path / "import"
    import_dir.mkdir()
    monkeypatch.setitem(settings.current, "default_rom_folder", str(rom_root))

    return {
        "import_dir": import_dir,
        "rom_root": rom_root,
        "log": [],
        "status": {},
    }


@scenario(
    "../features/organizer.feature",
    "Organiser moves a ROM straight into its system folder",
)
def test_organiser_moves_rom():
    pass


@scenario("../features/organizer.feature", "Dry run leaves every file where it is")
def test_dry_run_leaves_files():
    pass


@scenario("../features/organizer.feature", "Organiser does not overwrite an existing ROM")
def test_organiser_does_not_overwrite():
    pass


scenarios("../features/organizer.feature")


@scenario(
    "../features/organizer.feature",
    "A disc image that can't be identified is left in place",
)
def test_unidentified_disc_left_in_place():
    pass


@scenario("../features/organizer.feature", "A zip holding one ROM is sorted by the ROM inside")
def test_zip_sorted_by_contents():
    pass


@scenario(
    "../features/organizer.feature",
    "A second copy of the same ROM is reported as a duplicate",
)
def test_duplicate_reported():
    pass


@scenario(
    "../features/organizer.feature",
    "A DAT match decides the system of a file with a shared extension",
)
def test_dat_match_decides_system():
    pass




@scenario(
    "../features/organizer.feature",
    "A missing disc is added back to an existing multi-disc game",
)
def test_missing_disc_added_back():
    pass


@scenario(
    "../features/organizer.feature",
    "A multi-disc game already in the library is left alone",
)
def test_existing_multi_disc_left_alone():
    pass


@scenario(
    "../features/organizer.feature",
    "A dry run shows the playlist a multi-disc game would get",
)
def test_dry_run_multi_disc_playlist():
    pass


@scenario(
    "../features/organizer.feature",
    "A GameCube disc image is identified from its header",
)
def test_gamecube_header_detected():
    pass


@scenario("../features/organizer.feature", "A PS2 disc image is identified from its header")
def test_ps2_header_detected():
    pass


def add_import_file(organiser_context, relative_path, content):
    path = organiser_context["import_dir"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


@given(parsers.parse('an import folder containing "{filename}" for track "{track}"'))
def import_folder_with_cue(organiser_context, filename, track):
    sheet = add_import_file(
        organiser_context,
        filename,
        f'FILE "{track}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'.encode(),
    )
    add_import_file(organiser_context, sheet.parent.relative_to(organiser_context["import_dir"]) / track, b"track data")
    organiser_context["import_file"] = sheet


@given(parsers.parse('an import folder containing a zip "{filename}" holding "{member}"'))
def import_folder_with_zip(organiser_context, filename, member):
    path = organiser_context["import_dir"] / filename
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(member, b"gba rom data")
        zf.writestr("readme.txt", b"downloaded from somewhere")


@given(parsers.parse('an import folder containing a GameCube disc image "{filename}"'))
def import_folder_with_gamecube_iso(organiser_context, filename):
    header = bytearray(0x40)
    header[GAMECUBE_MAGIC_OFFSET : GAMECUBE_MAGIC_OFFSET + 4] = GAMECUBE_MAGIC
    add_import_file(organiser_context, filename, bytes(header))


@given(parsers.parse('an import folder containing a PS2 disc image "{filename}"'))
def import_folder_with_ps2_iso(organiser_context, filename):
    # ISO 9660 primary volume descriptor naming the PlayStation, then the
    # SYSTEM.CNF line PS2 discs boot from
    image = bytearray(0x9000)
    image[0x8000:0x8006] = b"\x01CD001"
    image[0x8008:0x8028] = b"PLAYSTATION".ljust(32)
    image += b"BOOT2 = cdrom0:\\SLUS_206.92;1\r\n"
    add_import_file(organiser_context, filename, bytes(image))


@given(parsers.parse('an import folder containing "{filename}"'))
def import_folder_with_rom(organiser_context, filename):
    organiser_context["import_file"] = add_import_file(
        organiser_context, filename, f"rom data for {filename}".encode()
    )


@given(parsers.parse('the import folder also contains "{filename}" with the same contents'))
def import_folder_also_contains_copy(organiser_context, filename):
    add_import_file(organiser_context, filename, organiser_context["import_file"].read_bytes())


@given(parsers.parse('the DATs list "{filename}" as "{name}" for "{system}" in "{dat_title}"'))
def dats_list_file(organiser_context, monkeypatch, filename, name, system, dat_title):
    contents = (organiser_context["import_dir"] / filename).read_bytes()
    monkeypatch.setitem(DAT_DB, hashlib.md5(contents).hexdigest(), (name, system, dat_title))


@given("the ES-DE folder layout")
def esde_folder_layout(monkeypatch):
    monkeypatch.setitem(settings.current, "multi_file_layout", "esde")


@given(parsers.parse('the import folder also contains "{filename}"'))
def import_folder_also_contains(organiser_context, filename):
    add_import_file(organiser_context, filename, f"rom data for {filename}".encode())


@given(parsers.parse('the ROM folder already contains "{relative_path}"'))
def rom_folder_has_existing(organiser_context, relative_path):
    existing = organiser_context["rom_root"] / relative_path
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(EXISTING_ROM_CONTENT)
    organiser_context["existing_rom"] = existing


@given(parsers.parse('the ROM folder already contains playlist "{relative_path}" listing "{entries}"'))
def rom_folder_has_playlist(organiser_context, relative_path, entries):
    playlist = organiser_context["rom_root"] / relative_path
    playlist.parent.mkdir(parents=True, exist_ok=True)
    playlist.write_text("".join(f"{entry}\n" for entry in entries.split(" | ")))


def run_organiser(organiser_context, dry_run):
    process_roms(
        organiser_context["import_dir"],
        lambda message, level="INFO": organiser_context["log"].append(message),
        organiser_context["status"],
        dry_run=dry_run,
    )


@when("the organiser runs")
def organiser_runs(organiser_context):
    run_organiser(organiser_context, dry_run=False)


@when("the organiser runs in dry-run mode")
def organiser_runs_dry(organiser_context):
    run_organiser(organiser_context, dry_run=True)


@then(parsers.parse('the ROM folder should contain "{relative_path}"'))
def rom_folder_contains(organiser_context, relative_path):
    assert (organiser_context["rom_root"] / relative_path).is_file()


@then(parsers.parse('the ROM folder should not contain "{relative_path}"'))
def rom_folder_lacks(organiser_context, relative_path):
    assert not (organiser_context["rom_root"] / relative_path).exists()


@then(parsers.parse("the status should count {count:d} {counter}"))
def status_counts(organiser_context, count, counter):
    assert organiser_context["status"].get(counter) == count


@then(parsers.parse('the playlist "{relative_path}" should list "{entries}"'))
def playlist_lists(organiser_context, relative_path, entries):
    playlist = organiser_context["rom_root"] / relative_path
    assert playlist.read_text().splitlines() == entries.split(" | ")
    # Every entry must resolve to a real file, relative to the playlist
    for entry in entries.split(" | "):
        assert (playlist.parent / entry).is_file()


@then(parsers.parse('the system folder "{system}" should only hold "{names}"'))
def system_folder_only_holds(organiser_context, system, names):
    folder = organiser_context["rom_root"] / system
    assert sorted(p.name for p in folder.iterdir()) == names.split(" | ")


@then("the import file should no longer exist")
def import_file_gone(organiser_context):
    assert not organiser_context["import_file"].exists()


@then("the import file should still exist")
def import_file_still_exists(organiser_context):
    assert organiser_context["import_file"].exists()


@then("the ROM folder should be empty")
def rom_folder_empty(organiser_context):
    assert list(organiser_context["rom_root"].iterdir()) == []


@then("the existing ROM should be unchanged")
def existing_rom_unchanged(organiser_context):
    assert organiser_context["existing_rom"].read_bytes() == EXISTING_ROM_CONTENT


@then(parsers.parse('the log should mention "{text}"'))
def log_mentions(organiser_context, text):
    assert any(text in message for message in organiser_context["log"])
