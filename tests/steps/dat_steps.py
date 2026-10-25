"""
Step implementations for DAT loading and fetching tests
"""

import io
import zipfile

import pytest
import requests
from pytest_bdd import given, scenario, scenarios, then, when, parsers

from modules.dat_fetcher import DATFetcher
from modules.dat_validation import (
    DAT_DB,
    fetch_latest_dats,
    load_dat_files,
    validate_hashes,
)

NO_INTRO_SHA1 = "6e4e9be9a07580ef267be9c2ea1bd0730b3be44a"
LIBRETRO_MD5 = "44091221ff27af8f274f210dec670bb1"


def quiet_logger(message, level="INFO"):
    pass


@pytest.fixture
def dat_context(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.dat_validation.DAT_DIR", tmp_path)
    monkeypatch.setattr("modules.dat_fetcher.DAT_DIR", tmp_path)
    return {"dat_dir": tmp_path, "downloads": []}


@scenario(
    "../features/dat.feature",
    "clrmamepro DATs with brackets in ROM names load their hashes",
)
def test_clrmamepro_brackets_and_metadat():
    pass


@scenario(
    "../features/dat.feature",
    "Pinned libretro DATs already on disk are not downloaded again",
)
def test_pinned_libretro_dats_skip_download():
    pass


@scenario("../features/dat.feature", "A failed libretro download keeps the existing DATs")
def test_failed_download_keeps_dats():
    pass


@scenario(
    "../features/dat.feature",
    "A failed libretro download points the user at manual DAT sources",
)
def test_failed_download_points_to_manual_sources():
    pass


scenarios("../features/dat.feature")


@given("a libretro DAT and a No-Intro metadat DAT exist")
def libretro_and_no_intro_dats(dat_context):
    dat_dir = dat_context["dat_dir"]

    libretro_dat = dat_dir / "libretro" / "dat" / "Nintendo - Game Boy.dat"
    libretro_dat.parent.mkdir(parents=True)
    libretro_dat.write_text(f"""clrmamepro (
	name "Nintendo - Game Boy"
)

game (
	name "Tetris (World)"
	description "Tetris (World) (Rev 1)"
	rom ( name "Tetris (World) (Rev 1).gb" size 32768 crc 46df91ad md5 {LIBRETRO_MD5} )
)
""")

    no_intro_dat = dat_dir / "metadat" / "no-intro" / "Nintendo - Game Boy Advance.dat"
    no_intro_dat.parent.mkdir(parents=True)
    no_intro_dat.write_text(f"""clrmamepro (
	name "Nintendo - Game Boy Advance"
)

game (
	name "Advance Wars (USA)"
	rom ( name "Advance Wars (USA).gba" size 8388608 crc caf2e99f sha1 {NO_INTRO_SHA1} )
)
""")


def write_dat(dat_context, relative_path, text):
    path = dat_context["dat_dir"] / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@given(parsers.parse('an XML DAT "{relative_path}" listing "{name}" with MD5 "{md5}"'))
def xml_dat(dat_context, relative_path, name, md5):
    write_dat(
        dat_context,
        relative_path,
        f'<?xml version="1.0"?>\n<datafile><game name="{name}">'
        f'<rom name="{name}.gb" md5="{md5}" /></game></datafile>\n',
    )


@given(
    parsers.parse(
        'a clrmamepro DAT "{relative_path}" with an unnamed game, a ROM without hashes '
        'and "{name}" with MD5 "{md5}"'
    )
)
def clrmamepro_dat_with_gaps(dat_context, relative_path, name, md5):
    write_dat(
        dat_context,
        relative_path,
        "clrmamepro (\n\tname \"Test\"\n)\n\n"
        "game (\n\tdescription \"No name here\"\n)\n\n"
        f"game (\n\tname \"{name}\"\n"
        "\trom ( name \"Bonus (Track 2).gb\" size 10 )\n"
        f"\trom ( name \"{name}.gb\" size 32768 crc 46df91ad md5 {md5} )\n)\n",
    )


@given(parsers.parse('a clrmamepro DAT "{relative_path}" with no hashes'))
def clrmamepro_dat_without_hashes(dat_context, relative_path):
    write_dat(
        dat_context,
        relative_path,
        'clrmamepro (\n\tname "Stub"\n)\n\ngame (\n\tname "NiGHTS"\n'
        '\trom (\n\t\tname "NiGHTS.iso"\n\t\tserial "81020"\n\t)\n)\n',
    )


@given(parsers.parse('an unreadable DAT "{name}"'))
def unreadable_dat(dat_context, name):
    # A folder that happens to be named like a DAT can't be read as one
    (dat_context["dat_dir"] / name).mkdir()


@when("the DAT files are loaded from the DAT directory")
def dat_files_loaded(dat_context):
    DAT_DB.clear()
    log = dat_context.setdefault("log", [])
    load_dat_files(lambda message, level="INFO": log.append(message))


@then(parsers.parse('MD5 "{md5}" should be "{name}" for "{system}" in "{dat_title}"'))
def md5_is_with_system(md5, name, system, dat_title):
    assert DAT_DB[md5] == (name, system, dat_title)


@then(parsers.parse('MD5 "{md5}" should be "{name}"'))
def md5_is(md5, name):
    assert validate_hashes({"md5": md5}) == name


@then(parsers.parse('MD5 "{md5}" should not be found'))
def md5_not_found(md5):
    assert validate_hashes({"md5": md5}) is None


@then(parsers.parse('the DAT log should mention "{text}" once'))
def dat_log_mentions_once(dat_context, text):
    assert sum(text in message for message in dat_context["log"]) == 1


@then(parsers.parse('the DAT log should mention "{text}"'))
def dat_log_mentions(dat_context, text):
    assert any(text in message for message in dat_context["log"])


@then(parsers.parse('the DAT log should not mention "{text}"'))
def dat_log_does_not_mention(dat_context, text):
    assert not any(text in message for message in dat_context["log"])


@then(parsers.parse('the hash lookup should return "{name}" for the No-Intro SHA1'))
def lookup_no_intro_sha1(name):
    assert validate_hashes({"sha1": NO_INTRO_SHA1}) == name


@then(parsers.parse('the hash lookup should return "{name}" for the libretro MD5'))
def lookup_libretro_md5(name):
    assert validate_hashes({"md5": LIBRETRO_MD5}) == name


def write_libretro_dats(dat_dir, commit):
    libretro_dir = dat_dir / "libretro"
    (libretro_dir / "dat").mkdir(parents=True)
    (libretro_dir / "dat" / "Existing.dat").write_text("existing")
    (libretro_dir / ".commit").write_text(commit)


@given("libretro DATs for the pinned commit are on disk")
def pinned_libretro_dats(dat_context):
    write_libretro_dats(dat_context["dat_dir"], DATFetcher.DEFAULT_LIBRETRO_COMMIT)


@given("libretro DATs from an older commit are on disk")
def older_libretro_dats(dat_context):
    write_libretro_dats(dat_context["dat_dir"], "0000000")


@given("downloads are recorded")
def downloads_recorded(dat_context, monkeypatch):
    def fake_get(url, **kwargs):
        dat_context["downloads"].append(url)
        raise requests.exceptions.ConnectionError("downloads disabled in tests")

    monkeypatch.setattr("modules.dat_fetcher.requests.get", fake_get)


@given("downloads fail")
def downloads_fail(dat_context, monkeypatch):
    downloads_recorded(dat_context, monkeypatch)


@when("the libretro DATs are fetched")
def libretro_dats_fetched(dat_context):
    dat_context["result"] = DATFetcher(quiet_logger).fetch_libretro_dats()


@when("the latest DATs are fetched")
def latest_dats_fetched(dat_context):
    log = dat_context.setdefault("log", [])
    dat_context["result"] = fetch_latest_dats(
        lambda message, level="INFO": log.append(message)
    )


@then("the latest DAT fetch should report success")
def latest_fetch_succeeded(dat_context):
    assert dat_context["result"] == {"libretro": True}


def libretro_archive(files):
    root = f"libretro-database-{DATFetcher.DEFAULT_LIBRETRO_COMMIT}/"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(root, b"")
        zf.writestr(root + "dat/", b"")
        for name in files:
            zf.writestr(root + name, b"dat contents")
    return buffer.getvalue()


DOWNLOADS = {
    "a libretro archive": libretro_archive(
        [
            "dat/Nintendo - Game Boy.dat",
            "metadat/no-intro/Nintendo - Game Boy Advance.dat",
            "metadat/redump/Sony - PlayStation.dat",
            "metadat/genre/Nintendo - Game Boy.dat",
            "rdb/Nintendo - Game Boy.rdb",
            "README.md",
        ]
    ),
    "a libretro archive without DATs": libretro_archive(["README.md"]),
    "an HTML page": b"<!DOCTYPE html><html>rate limited</html>",
    "a damaged zip": b"PK\x03\x04 truncated",
}


class FakeDownload:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


@given(parsers.parse("the download returns {download}"))
def download_returns(dat_context, monkeypatch, download):
    content = DOWNLOADS[download]

    def fake_get(url, **kwargs):
        dat_context["downloads"].append(url)
        return FakeDownload(content)

    monkeypatch.setattr("modules.dat_fetcher.requests.get", fake_get)


@given("a leftover staging folder from an earlier download")
def leftover_staging(dat_context):
    staging = dat_context["dat_dir"] / "libretro.partial" / "dat"
    staging.mkdir(parents=True)
    (staging / "Half Written.dat").write_text("partial")


@then("the libretro folder should hold exactly")
def libretro_folder_holds(dat_context, datatable):
    libretro_dir = dat_context["dat_dir"] / "libretro"
    files = sorted(
        p.relative_to(libretro_dir).as_posix() for p in libretro_dir.rglob("*") if p.is_file()
    )
    assert files == sorted(path for (path,) in datatable[1:])


@then("the commit marker should name the pinned commit")
def commit_marker_pinned(dat_context):
    marker = dat_context["dat_dir"] / "libretro" / ".commit"
    assert marker.read_text() == DATFetcher.DEFAULT_LIBRETRO_COMMIT


@then("no staging folder should be left behind")
def no_staging_left(dat_context):
    staging = dat_context["dat_dir"] / "libretro.partial"
    assert not staging.exists() or not any(staging.rglob("*.dat"))


@then("only the libretro archive should be requested")
def only_libretro_requested(dat_context):
    assert dat_context["result"] == {"libretro": False}
    # Only the free GitHub sources: one libretro archive, and FinalBurn Neo's DATs
    libretro = [url for url in dat_context["downloads"] if "libretro-database" in url]
    assert len(libretro) == 1
    assert all(url.startswith(("https://github.com/", "https://raw.githubusercontent.com/"))
               for url in dat_context["downloads"])


@then("the log should explain where to put manually downloaded DATs")
def log_explains_manual_dats(dat_context):
    manual_help = [m for m in dat_context["log"] if "To add DATs manually" in m]
    assert manual_help
    assert str(dat_context["dat_dir"] / "metadat" / "no-intro") in manual_help[0]


@then("no download should be attempted")
def no_download_attempted(dat_context):
    assert dat_context["downloads"] == []


@then("the libretro fetch should report success")
def libretro_fetch_succeeded(dat_context):
    assert dat_context["result"] == {"libretro": True}


@then("the libretro fetch should report failure")
def libretro_fetch_failed(dat_context):
    assert dat_context["result"] == {"libretro": False}


@then("the existing libretro DATs should be kept")
def existing_libretro_dats_kept(dat_context):
    assert (dat_context["dat_dir"] / "libretro" / "dat" / "Existing.dat").exists()


@given(parsers.parse('a clrmamepro DAT "{relative_path}" with no games'))
def clrmamepro_dat_without_games(dat_context, relative_path):
    write_dat(dat_context, relative_path, 'clrmamepro (\n\tname "Stub"\n)\n')


@then(parsers.parse('the name "{name}" should be found for "{system}"'))
def name_found_for(name, system):
    from modules.dat_validation import lookup_name, name_key

    found, found_system, _ = lookup_name(name, system)
    assert name_key(found) == name_key(name)
    assert found_system == system


@then(parsers.parse('the name "{name}" should not be found for "{system}"'))
def name_not_found_for(name, system):
    from modules.dat_validation import lookup_name

    assert lookup_name(name, system) == (None, None, None)


@then(parsers.parse('the name "{name}" should not be found without a system'))
def name_not_found_alone(name):
    from modules.dat_validation import lookup_name

    assert lookup_name(name) == (None, None, None)


@then(parsers.parse('the name "{name}" should be found without a system as "{found}"'))
def name_found_alone(name, found):
    from modules.dat_validation import lookup_name

    assert lookup_name(name)[0] == found


@given(parsers.parse('an XML DAT "{relative_path}" listing the games "{names}"'))
def xml_dat_games(dat_context, relative_path, names):
    games = "".join(
        f'<game name="{name}"><rom name="{name}.iso" md5="{index:032x}" /></game>'
        for index, name in enumerate(names.split(" | "), start=1)
    )
    write_dat(dat_context, relative_path, f'<?xml version="1.0"?>\n<datafile>{games}</datafile>\n')


@then(parsers.parse('the name "{name}" should be found for "{system}" as "{found}"'))
def name_found_for_as(name, system, found):
    from modules.dat_validation import lookup_name

    assert lookup_name(name, system)[0] == found


class FakeDownload:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


@given("FinalBurn Neo's DATs can be downloaded")
def fbneo_downloadable(dat_context, monkeypatch):
    def fake_get(url, **kwargs):
        dat_context["downloads"].append(url)
        return FakeDownload(f"<datafile><!-- {url} --></datafile>".encode())

    monkeypatch.setattr("modules.dat_fetcher.requests.get", fake_get)


@given("FinalBurn Neo's DATs for the pinned commit are on disk")
def fbneo_on_disk(dat_context):
    folder = dat_context["dat_dir"] / "fbneo"
    folder.mkdir(parents=True)
    for name in DATFetcher.FBNEO_DATS:
        (folder / name).write_text("<datafile />")
    (folder / ".commit").write_text(DATFetcher.DEFAULT_FBNEO_COMMIT)


@when("FinalBurn Neo's DATs are fetched")
def fbneo_fetched(dat_context):
    dat_context["result"] = DATFetcher(quiet_logger).fetch_fbneo_dats()


@then(parsers.parse("FinalBurn Neo's fetch should report {outcome}"))
def fbneo_result(dat_context, outcome):
    assert dat_context["result"] is (outcome == "success")


@then("FinalBurn Neo's DATs should be on disk")
def fbneo_files_on_disk(dat_context):
    folder = dat_context["dat_dir"] / "fbneo"
    assert sorted(p.name for p in folder.glob("*.dat")) == sorted(DATFetcher.FBNEO_DATS)
    assert (folder / ".commit").read_text() == DATFetcher.DEFAULT_FBNEO_COMMIT
    assert not (dat_context["dat_dir"] / "fbneo.partial").exists()


@given(parsers.parse('FinalBurn Neo\'s "{kind}" DAT lists "{zip_name}" as "{description}"'))
def fbneo_dat(dat_context, kind, zip_name, description):
    name = f"FinalBurn Neo (ClrMame Pro XML, {kind}).dat"
    write_dat(
        dat_context,
        f"fbneo/{name}",
        f'<?xml version="1.0"?><datafile><game name="{zip_name}"><description>{description}</description>'
        f'<rom name="{zip_name}.bin" crc="12345678" /></game></datafile>',
    )


@given(parsers.parse('an extra DAT "{name}" whose {element} "{game}" has MD5 "{md5}"'))
def extra_dat(dat_context, name, element, game, md5):
    write_dat(
        dat_context,
        f"extra/{name}",
        f'<?xml version="1.0"?><datafile><{element} name="{game}"><description>{game} (Full Title)</description>'
        f'<rom name="{game}.bin" md5="{md5}" /></{element}></datafile>',
    )


@then(parsers.parse('the name "{name}" should be found for "{system}" as "{found}" in "{dat_title}"'))
def name_found_with_title(name, system, found, dat_title):
    from modules.dat_validation import lookup_name

    assert lookup_name(name, system) == (found, system, dat_title)


@then(parsers.parse('MD5 "{md5}" should be "{name}" for "{system}" with no thumbnail folder'))
def md5_without_thumbnails(md5, name, system):
    assert DAT_DB[md5] == (name, system, None)
