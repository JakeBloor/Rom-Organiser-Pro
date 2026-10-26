"""
Step implementations for ROM organiser tests
"""

import hashlib
import zipfile

import pytest
from pytest_bdd import given, scenario, scenarios, then, when, parsers

from modules import settings

from modules.dat_validation import DAT_DB
from modules.cache import FileCache
from modules.library import pending_games
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
        "cache": FileCache(tmp_path / "cache" / "files.json"),
        "hashed": [],
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


@given(parsers.parse('"{relative_path}" is dropped into the ROM folder'))
def dropped_into_rom_folder(organiser_context, relative_path):
    path = organiser_context["rom_root"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"rom {path.stem}".encode())


@given(parsers.parse('a copy of "{source}" is dropped into the ROM folder as "{relative_path}"'))
def copy_dropped_into_rom_folder(organiser_context, source, relative_path):
    root = organiser_context["rom_root"]
    (root / relative_path).write_bytes((root / source).read_bytes())


@given("ROM hashing is counted")
def hashing_counted(organiser_context, monkeypatch):
    from modules import organizer

    real_hash_rom = organizer.hash_rom

    def counting_hash_rom(path, progress=None):
        organiser_context["hashed"].append(path)
        return real_hash_rom(path, progress)

    monkeypatch.setattr(organizer, "hash_rom", counting_hash_rom)


def organise_rom_folder(organiser_context, dry_run=False):
    root = organiser_context["rom_root"]
    files = [f for game, tracks in pending_games(root).items() for f in [game, *tracks]]
    organiser_context["placed"] = process_roms(
        root,
        lambda message, level="INFO": organiser_context["log"].append(message),
        organiser_context["status"],
        dry_run=dry_run,
        rom_root=root,
        files=files,
        cache=organiser_context["cache"],
    )


@given("the ROM folder is organised")
@when("the ROM folder is organised")
def rom_folder_organised(organiser_context):
    organise_rom_folder(organiser_context)


@when("the ROM folder is organised in dry-run mode")
def rom_folder_organised_dry_run(organiser_context):
    organise_rom_folder(organiser_context, dry_run=True)


@when(parsers.parse('"{relative_path}" is changed'))
def file_changed(organiser_context, relative_path):
    path = organiser_context["rom_root"] / relative_path
    path.write_bytes(path.read_bytes() + b" changed")


@then(parsers.parse('the folder "{relative_path}" should be gone'))
def folder_gone(organiser_context, relative_path):
    assert not (organiser_context["rom_root"] / relative_path).exists()


@then(parsers.parse('the cache should say "{relative_path}" was {outcome}'))
def cache_outcome(organiser_context, relative_path, outcome):
    entry = organiser_context["cache"].get(organiser_context["rom_root"] / relative_path)
    assert entry["outcome"] == outcome


@then(parsers.re(r"(?P<count>\d+) files? should have been hashed"))
def files_hashed(organiser_context, count):
    assert len(organiser_context["hashed"]) == int(count)


@then("no duplicates should be reported")
def no_duplicates(organiser_context):
    assert organiser_context["status"].get("duplicates", 0) == 0
    assert not any("[DUPLICATE]" in message for message in organiser_context["log"])


@given(parsers.parse('the DATs list "{relative_path}" in the ROM folder as "{name}" for "{system}" in "{dat_title}"'))
def dats_list_rom_folder_file(organiser_context, monkeypatch, relative_path, name, system, dat_title):
    contents = (organiser_context["rom_root"] / relative_path).read_bytes()
    monkeypatch.setitem(DAT_DB, hashlib.md5(contents).hexdigest(), (name, system, dat_title))


@then("the placed game should have no DAT name")
def placed_game_has_no_dat_name(organiser_context):
    (game,) = organiser_context["placed"]
    assert game["dat_title"] is None
    assert game["names"] == ["Chrono Trigger (USA)"]


@given(parsers.parse("files up to {megabytes:d} MB are checked against the DATs"))
def dat_check_limit(monkeypatch, megabytes):
    monkeypatch.setitem(settings.current, "dat_check_limit_mb", megabytes)


@given(parsers.parse('a {megabytes:d} MB "{relative_path}" is dropped into the ROM folder'))
def big_file_dropped(organiser_context, megabytes, relative_path):
    path = organiser_context["rom_root"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(path.stem.encode().ljust(megabytes * 1024 * 1024, b"\0"))


@given(parsers.parse("reading happens in {megabytes:d} MB chunks"))
def reading_chunks(organiser_context, monkeypatch, megabytes):
    monkeypatch.setattr("modules.hashing.CHUNK_SIZE", megabytes * 1024 * 1024)
    # The big file must be read in full to see its progress
    monkeypatch.setitem(settings.current, "dat_check_limit_mb", 1000)
    details = organiser_context["details"] = []

    class RecordingStatus(dict):
        def __setitem__(self, key, value):
            if key == "current_detail" and value:
                details.append(value)
            super().__setitem__(key, value)

    organiser_context["status"] = RecordingStatus()


@given("a stop has been requested")
def stop_requested(organiser_context):
    organiser_context["status"]["cancel_requested"] = True


@then(parsers.parse('the cache should hold a fingerprint for "{relative_path}"'))
def cache_holds_fingerprint(organiser_context, relative_path):
    entry = organiser_context["cache"].get(organiser_context["rom_root"] / relative_path)
    assert entry["identity"].startswith("fp:")
    assert "md5" not in entry


@then(parsers.parse('the cache should know nothing about "{relative_path}"'))
def cache_knows_nothing(organiser_context, relative_path):
    assert organiser_context["cache"].get(organiser_context["rom_root"] / relative_path) is None


@then(parsers.parse('the games should have been organised in the order "{systems}"'))
def organised_in_order(organiser_context, systems):
    assert [game["system"] for game in organiser_context["placed"]] == systems.split(", ")


@then(parsers.parse('the progress should have shown "{detail}"'))
def progress_shown(organiser_context, detail):
    assert detail in organiser_context["details"]


@then(parsers.parse('{done:g} GB of {size:g} GB should read as "{text}"'))
def gigabytes_read_as(done, size, text):
    from modules.organizer import _size

    gb = 1024 ** 3
    assert f"{_size(done * gb, size * gb)} of {_size(size * gb, size * gb)}" == text


@given(parsers.parse('a PS3 disc folder "{relative_path}" titled "{title}" with {count:d} files is dropped into the ROM folder'))
def ps3_disc_folder(organiser_context, relative_path, title, count):
    from tests.sfo import make_sfo

    folder = organiser_context["rom_root"] / relative_path / "PS3_GAME"
    (folder / "USRDIR").mkdir(parents=True)
    (folder / "PARAM.SFO").write_bytes(make_sfo({"TITLE": title}))
    for index in range(count):
        (folder / "USRDIR" / f"DATA{index:04}.BIN").write_bytes(b"data")


@given(parsers.parse('a PS3 game folder "{relative_path}" is dropped into the ROM folder'))
def ps3_game_folder(organiser_context, relative_path):
    eboot = organiser_context["rom_root"] / relative_path / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"
    eboot.parent.mkdir(parents=True)
    eboot.write_bytes(b"eboot")


@then(parsers.parse('the placed games should be titled "{titles}"'))
def placed_titles(organiser_context, titles):
    assert sorted(game["title"] for game in organiser_context["placed"]) == titles.split(", ")


@then("nothing should be waiting to be organised")
def nothing_waiting(organiser_context):
    assert pending_games(organiser_context["rom_root"], organiser_context["cache"]) == {}


@given(parsers.parse('the DATs know "{name}" for "{system}" in "{dat_title}" by name'))
def dats_know_name(monkeypatch, name, system, dat_title):
    from modules.dat_validation import DAT_NAMES, name_key

    monkeypatch.setitem(DAT_NAMES, name_key(name), {system: (name, system, dat_title)})


@given(parsers.parse('a CHD "{relative_path}" whose header records SHA-1 "{sha1}"'))
def chd_dropped(organiser_context, relative_path, sha1):
    header = bytearray(0x7C)
    header[:8] = b"MComprHD"
    header[12:16] = (5).to_bytes(4, "big")
    header[0x40:0x54] = bytes.fromhex(sha1)
    path = organiser_context["rom_root"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + b"hunks")


@given(parsers.parse('the DATs list SHA-1 "{sha1}" as "{name}" for "{system}" in "{dat_title}"'))
def dats_list_sha1(monkeypatch, sha1, name, system, dat_title):
    monkeypatch.setitem(DAT_DB, sha1, (name, system, dat_title))


@given(parsers.parse('"{relative_path}" is dropped into the ROM folder with a 512-byte copier header'))
def snes_with_header(organiser_context, relative_path):
    path = organiser_context["rom_root"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    organiser_context["headerless"] = b"chrono" * 2048
    path.write_bytes(b"\0" * 512 + organiser_context["headerless"])


@given(parsers.parse('the DATs list the ROM without its header as "{name}" for "{system}" in "{dat_title}"'))
def dats_list_headerless(organiser_context, monkeypatch, name, system, dat_title):
    digest = hashlib.md5(organiser_context["headerless"]).hexdigest()
    monkeypatch.setitem(DAT_DB, digest, (name, system, dat_title))


@then(parsers.parse('the placed game should come from the DAT "{dat_title}"'))
def placed_from_dat(organiser_context, dat_title):
    (game,) = organiser_context["placed"]
    assert game["dat_title"] == dat_title


@then("the DAT misses should be")
def dat_misses_are(organiser_context, datatable):
    expected = {reason: int(games) for reason, games in datatable[1:]}
    assert organiser_context["status"]["dat_misses"] == expected


@given(parsers.parse('the DATs know serial "{serial}" as "{name}" for "{system}" in "{dat_title}"'))
def dats_know_serial(monkeypatch, serial, name, system, dat_title):
    from modules import dat_validation

    monkeypatch.setattr(dat_validation, "DAT_SERIALS", {})
    dat_validation._add_serials((name, system, dat_title), f'serial "{serial}"')


@given(parsers.parse('a Wii-style image "{relative_path}" with game ID "{game_id}" is dropped into the ROM folder'))
def nintendo_image(organiser_context, relative_path, game_id):
    header = bytearray(0x58 + 0x20)
    header[:4] = b"RVZ\x01"
    header[0x58:0x5E] = game_id.encode()
    header[0x58 + 0x1C:0x58 + 0x20] = bytes.fromhex("C2339F3D")
    path = organiser_context["rom_root"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + b"compressed")


@given(parsers.parse('a PS3 disc folder "{relative_path}" with serial "{serial}" is dropped into the ROM folder'))
def ps3_disc_with_serial(organiser_context, relative_path, serial):
    from tests.sfo import make_sfo

    folder = organiser_context["rom_root"] / relative_path / "PS3_GAME"
    folder.mkdir(parents=True)
    (folder / "PARAM.SFO").write_bytes(make_sfo({"TITLE_ID": serial, "TITLE": "DEMONS SOULS"}))


@given(parsers.parse('the DATs know "{zip_name}" as "{title}" for "{system}" in "{dat_title}" by zip name'))
def dats_know_zip(monkeypatch, zip_name, title, system, dat_title):
    from modules.dat_validation import DAT_NAMES, name_key

    monkeypatch.setitem(DAT_NAMES, name_key(zip_name), {system: (title, system, dat_title)})


@then(parsers.parse('the sheet "{relative_path}" should point at "{tracks}"'))
def sheet_points_at_track(organiser_context, relative_path, tracks):
    from modules.archives import sheet_tracks

    sheet = organiser_context["rom_root"] / relative_path
    tracks = tracks.split(" | ")
    for track in tracks:
        assert f'"{track}"' in sheet.read_text()
    assert [t.resolve() for t in sheet_tracks(sheet)] == [(sheet.parent / t).resolve() for t in tracks]


@given(parsers.parse('"{relative_path}" in the ROM folder points at "{tracks}"'))
def sheet_in_rom_folder(organiser_context, relative_path, tracks):
    sheet = organiser_context["rom_root"] / relative_path
    sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.write_text("".join(f'FILE "{track}" BINARY\n  TRACK 01 MODE1/2352\n' for track in tracks.split(" | ")))


@given(parsers.parse('"{relative_path}" in the ROM folder lists "{entries}"'))
def playlist_in_rom_folder(organiser_context, relative_path, entries):
    playlist = organiser_context["rom_root"] / relative_path
    playlist.parent.mkdir(parents=True, exist_ok=True)
    playlist.write_text("".join(entry + "\n" for entry in entries.split(" | ")))


def repair(organiser_context, dry_run):
    from modules.organizer import repair_playlists

    organiser_context["repaired"] = repair_playlists(
        organiser_context["rom_root"],
        lambda message, level="INFO": organiser_context["log"].append(message),
        dry_run,
    )


@when("the playlists are repaired")
def playlists_repaired(organiser_context):
    repair(organiser_context, dry_run=False)


@when("the playlists are repaired in dry-run mode")
def playlists_repaired_dry_run(organiser_context):
    repair(organiser_context, dry_run=True)


@then(parsers.parse("{count:d} playlist should have been repaired"))
def playlists_repaired_count(organiser_context, count):
    assert organiser_context["repaired"] == count


@then(parsers.parse('the playlist "{relative_path}" should still read "{entries}"'))
def playlist_reads(organiser_context, relative_path, entries):
    playlist = organiser_context["rom_root"] / relative_path
    assert playlist.read_text().splitlines() == entries.split(" | ")


@then(parsers.parse('the log should include "{line}"'))
def log_includes(organiser_context, line):
    assert line in organiser_context["log"], organiser_context["log"]


@then(parsers.parse('the log should include a line starting "{start}"'))
def log_includes_start(organiser_context, start):
    assert any(message.startswith(start) for message in organiser_context["log"]), organiser_context["log"]
