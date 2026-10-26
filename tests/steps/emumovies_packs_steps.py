"""
Step implementations for EmuMovies artwork packs and the local library they fill
"""

import io
import json
import zipfile
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import emumovies, emumovies_packs, settings
from modules.media import esde_media_path
from tests.emumovies_fakes import FakeFTP, FakeFTPTLS, FakeServer


@pytest.fixture
def pack_context(tmp_path, monkeypatch):
    server = FakeServer()
    FakeFTP.server = server
    monkeypatch.setattr("modules.emumovies.ftplib.FTP", FakeFTP)
    monkeypatch.setattr("modules.emumovies.ftplib.FTP_TLS", FakeFTPTLS)
    return {
        "tmp": tmp_path,
        "server": server,
        "rom_root": tmp_path / "roms",
        "library": tmp_path / "library",
        "media_root": tmp_path / "downloaded_media",
        "log": [],
    }


scenarios("../features/emumovies_packs.feature")


def logger(pack_context):
    return lambda message, level="INFO": pack_context["log"].append(message)


def zip_bytes(names):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        for name in names:
            archive.writestr(f"pack folder/{name}", f"image {name}")
    return data.getvalue()


@given("a system's artwork files")
def artwork_files(pack_context, datatable):
    pack_context["files"] = [row[0] for row in datatable[1:]]


@given(parsers.parse('a ROM folder with "{first}" and "{second}" games'))
def rom_folder(pack_context, first, second):
    for system in (first, second):
        (pack_context["rom_root"] / system).mkdir(parents=True)


@given(parsers.re(r'EmuMovies has the "(?P<system>[^"]+)" pack "(?P<name>[^"]+)" in (?P<count>\d+) parts? holding "(?P<images>[^"]+)"'))
def emumovies_pack(pack_context, system, name, count, images):
    count = int(count)
    server = pack_context["server"]
    data = zip_bytes(images.split(", "))
    size = len(data) // count + 1
    folder = f"Official/Artwork/{system}"
    server.tree.setdefault("Official/Artwork", [])
    if system not in server.tree["Official/Artwork"]:
        server.tree["Official/Artwork"].append(system)
    if "Artwork" not in server.tree["Official"]:
        server.tree["Official"].append("Artwork")
    # A newer version replaces the old one on the server
    server.tree[folder] = [f for f in server.tree.get(folder, []) if emumovies_packs.pack_type(f) != emumovies_packs.pack_type(name)]
    for index in range(count):
        part = f"{name}.part{index + 1}.rar" if count > 1 else f"{name}.rar"
        server.tree[folder].append(part)
        server.files[f"{folder}/{part}"] = data[index * size:(index + 1) * size]


@given("EmuMovies pack downloads fail")
def pack_downloads_fail(pack_context):
    pack_context["server"].download_error = "connection reset"


@given("the pack on EmuMovies is damaged")
def pack_damaged(pack_context):
    for path in pack_context["server"].files:
        pack_context["server"].files[path] = b"not an archive" * 100


def download(pack_context, stop=False):
    # A fresh listing each time, as a day apart, so a newer pack on the server is seen
    pack_context["downloads"] = pack_context.get("downloads", 0) + 1
    listings = pack_context["tmp"] / f"listings-{pack_context['downloads']}.json"
    server = emumovies.EmuMoviesServer("ftp.example", "player", "secret", logger(pack_context), listings)
    server.connect()
    pack_context["details"] = []
    pack_context["summary"] = emumovies_packs.download_packs(
        server,
        pack_context["rom_root"],
        emumovies_packs.ArtworkLibrary(pack_context["library"]),
        logger(pack_context),
        progress=pack_context["details"].append,
        should_stop=lambda: stop,
    )
    server.close()


@given("the artwork packs have been downloaded")
@when("the artwork packs are downloaded")
def packs_downloaded(pack_context):
    download(pack_context)


@when("the artwork packs are downloaded after a stop request")
def packs_downloaded_stopped(pack_context):
    download(pack_context, stop=True)


@when("the packs are chosen")
def packs_chosen(pack_context):
    pack_context["chosen"] = emumovies_packs.choose_packs(pack_context["files"])


@given(parsers.parse('ES-DE keeps its media in "{folder}"'))
def esde_media(pack_context, monkeypatch, folder):
    monkeypatch.setitem(settings.current, "emumovies_artwork_dir", "")
    monkeypatch.setattr(emumovies_packs.esde, "media_root", lambda: pack_context["tmp"] / folder)


@when(parsers.parse('the pack library is set to "{folder}"'))
def library_set(monkeypatch, folder):
    monkeypatch.setitem(settings.current, "emumovies_artwork_dir", folder)


@given(parsers.parse('the library holds "{first}" and "{second}"'))
def library_holds(pack_context, first, second):
    for relative in (first, second):
        path = pack_context["library"] / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"library {relative}".encode())


@given(parsers.parse('"{game_path}" already has an ES-DE "{media_type}" image'))
def already_has_image(pack_context, game_path, media_type):
    path = esde_media_path(pack_context["media_root"], game_path.split("/")[0], game_path, media_type, ".png")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"existing")


@given("files can't be linked")
def no_links(monkeypatch):
    def refuse(source, destination):
        raise OSError("cross-device link")

    monkeypatch.setattr("modules.emumovies.os.link", refuse)


@when(parsers.parse('images are filled from the library for "{game_path}" named "{name}"'))
def images_filled(pack_context, game_path, name):
    game = {"system": game_path.split("/")[0], "names": [name], "path": Path(game_path)}
    pack_context["game"] = game
    library = pack_context["shared_library"] = emumovies_packs.ArtworkLibrary(pack_context["library"])
    pack_context["filled"] = emumovies.fetch_emumovies(
        game, pack_context["media_root"], None, logger(pack_context), library,
    )


@then("the chosen packs should be")
def chosen_packs(pack_context, datatable):
    expected = {media_type: (pack, parts.split(", ")) for media_type, pack, parts in datatable[1:]}
    assert pack_context["chosen"] == expected


@then(parsers.parse('the "{media_type}" pack should be "{name}"'))
def chosen_pack(pack_context, media_type, name):
    assert pack_context["chosen"][media_type][0] == name


@then(parsers.parse('the library should hold "{files}"'))
def library_files(pack_context, files):
    library = pack_context["library"]
    found = sorted(
        p.relative_to(library).as_posix() for p in library.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    )
    assert found == files.split(", ")


@then(parsers.parse('the manifest should say "{folder}" came from "{pack}" with {count:d} images'))
def manifest_says(pack_context, folder, pack, count):
    manifest = json.loads((pack_context["library"] / "manifest.json").read_text())
    assert (manifest[folder]["pack"], manifest[folder]["files"]) == (pack, count)


@then("no downloaded parts or unpacking folders should be left")
def no_leftovers(pack_context):
    library = pack_context["library"]
    for folder in (".downloads", ".unpacking"):
        assert not any((library / folder).rglob("*")) if (library / folder).exists() else True


@then(parsers.parse("the pack summary should be {installed:d} installed, {up_to_date:d} up to date and {failed:d} failed"))
def pack_summary(pack_context, installed, up_to_date, failed):
    assert pack_context["summary"] == {"installed": installed, "up_to_date": up_to_date, "failed": failed}


@then(parsers.parse('the pack log should mention "{text}"'))
def pack_log(pack_context, text):
    assert any(text in message for message in pack_context["log"])


@then("nothing on the EmuMovies server should have been changed by the packs")
def server_unchanged(pack_context):
    assert pack_context["server"].changes == []
    assert any("MB" in detail for detail in pack_context["details"])


@then(parsers.parse('the pack library should be "{folder}" expanded'))
def library_expanded(folder):
    assert emumovies_packs.library_root() == Path(folder).expanduser()


@then(parsers.parse('the pack library should be "{folder}"'))
def library_is(pack_context, folder):
    assert emumovies_packs.library_root() == pack_context["tmp"] / folder


@then(parsers.parse('the library should have filled "{media}"'))
def library_filled(pack_context, media):
    assert pack_context["filled"] == media.split(", ")


@then("the library should have filled nothing")
def library_filled_nothing(pack_context):
    assert pack_context["filled"] == []


def filled_image(pack_context, media_type):
    game = pack_context["game"]
    return esde_media_path(pack_context["media_root"], game["system"], game["path"], media_type, ".png")


@then(parsers.parse('the ES-DE "{media_type}" image should be linked to the library\'s'))
def image_linked(pack_context, media_type):
    image = filled_image(pack_context, media_type)
    source = pack_context["library"] / "psx" / media_type / "Spyro the Dragon (USA).png"
    assert image.stat().st_ino == source.stat().st_ino


@then(parsers.parse('the ES-DE "{media_type}" image should be a copy of the library\'s'))
def image_copied(pack_context, media_type):
    image = filled_image(pack_context, media_type)
    source = pack_context["library"] / "psx" / media_type / "Spyro the Dragon (USA).png"
    assert image.read_bytes() == source.read_bytes()
    assert image.stat().st_ino != source.stat().st_ino


@when(parsers.parse('images are filled from the same library for "{game_path}" named "{name}"'))
def images_filled_same_library(pack_context, game_path, name):
    game = {"system": game_path.split("/")[0], "names": [name], "path": Path(game_path)}
    pack_context["game"] = game
    pack_context["filled"] = emumovies.fetch_emumovies(
        game, pack_context["media_root"], None, logger(pack_context), pack_context["shared_library"],
    )
