"""
Step implementations for videos and manuals from EmuMovies, against a fake file server
"""

import json
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import emumovies, settings
from modules.media import ESDE_MEDIA_TYPES, esde_media_path
from tests.emumovies_fakes import FakeFTP, FakeFTPTLS, FakeServer


@pytest.fixture
def em_context(tmp_path, monkeypatch):
    server = FakeServer()
    FakeFTP.server = server
    monkeypatch.setattr("modules.emumovies.ftplib.FTP", FakeFTP)
    monkeypatch.setattr("modules.emumovies.ftplib.FTP_TLS", FakeFTPTLS)
    monkeypatch.setattr("modules.emumovies.LISTING_CACHE", tmp_path / "cache" / "emumovies.json")
    return {
        "server": server,
        "media_root": tmp_path / "downloaded_media",
        "cache": tmp_path / "cache" / "emumovies.json",
        "log": [],
    }


scenarios("../features/emumovies.feature")


def logger(em_context):
    return lambda message, level="INFO": em_context["log"].append(message)


def turn_on(monkeypatch, quality="HQ"):
    for key, value in {
        "enable_emumovies": True,
        "emumovies_host_main": "ftp.example",
        "emumovies_user": "player",
        "emumovies_password": "secret",
        "emumovies_video_quality": quality,
    }.items():
        monkeypatch.setitem(settings.current, key, value)


def open_server(em_context):
    connection = emumovies.EmuMoviesServer("ftp.example", "player", "secret", logger(em_context), em_context["cache"])
    connection.connect()
    em_context["connection"] = connection
    return connection


@given("EmuMovies has the sets")
def emumovies_sets(em_context, datatable):
    server = em_context["server"]
    for folder, set_name, file in datatable[1:]:
        kind_path = f"Official/{folder}"
        set_path = f"{kind_path}/{set_name}"
        if folder not in server.tree["Official"]:
            server.tree["Official"].append(folder)
        if set_name not in server.tree.setdefault(kind_path, []):
            server.tree[kind_path].append(set_name)
        server.tree.setdefault(set_path, []).append(file)
        server.files[f"{set_path}/{file}"] = f"{set_path}/{file}".encode()


@given(parsers.parse('EmuMovies is set up with video quality "{quality}"'))
def emumovies_set_up(em_context, monkeypatch, quality):
    turn_on(monkeypatch, quality)
    open_server(em_context)


@given(parsers.parse("{kind} from EmuMovies are switched off"))
def kind_off(monkeypatch, kind):
    monkeypatch.setitem(settings.current, f"emumovies_{kind}", False)


@given(parsers.parse('"{game_path}" already has ES-DE "{media_type}"'))
def already_has_media(em_context, game_path, media_type):
    suffix = ESDE_MEDIA_TYPES[media_type][0]
    path = esde_media_path(em_context["media_root"], game_path.split("/")[0], game_path, media_type, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"existing")


@given(parsers.parse('EmuMovies downloads fail with "{message}"'))
def downloads_fail(em_context, message):
    em_context["server"].download_error = message


@given(parsers.parse('the EmuMovies folder "{path}" can\'t be listed'))
def folder_unlistable(em_context, path):
    em_context["server"].unlistable.add(path)


@given("the EmuMovies server has gone away")
def server_gone(em_context):
    em_context["server"].gone = True


@given(parsers.re(r"EmuMovies is (?P<state>switched off|switched on without a login|set up and allows encryption|set up but refuses encryption|set up with a wrong password)$"))
def emumovies_state(em_context, monkeypatch, state):
    if state == "switched off":
        monkeypatch.setitem(settings.current, "enable_emumovies", False)
    elif state == "switched on without a login":
        monkeypatch.setitem(settings.current, "enable_emumovies", True)
    else:
        turn_on(monkeypatch)
        em_context["server"].refuse_tls = state == "set up but refuses encryption"
        em_context["server"].wrong_password = state == "set up with a wrong password"


@given("EmuMovies is set up with a main server that's down and a working backup")
def main_down_backup_up(em_context, monkeypatch):
    turn_on(monkeypatch)
    monkeypatch.setitem(settings.current, "emumovies_host_main", "main.example")
    monkeypatch.setitem(settings.current, "emumovies_host_backup", "backup.example")
    em_context["server"].down_hosts.add("main.example")


@given("EmuMovies is set up with only a backup server")
def only_backup(em_context, monkeypatch):
    turn_on(monkeypatch)
    monkeypatch.setitem(settings.current, "emumovies_host_main", "")
    monkeypatch.setitem(settings.current, "emumovies_host_backup", "backup.example")


@given("an EmuMovies connection that never logged in")
def never_logged_in(em_context):
    em_context["connection"] = emumovies.EmuMoviesServer(
        "ftp.example", "player", "secret", logger(em_context), em_context["cache"]
    )


def fetch(em_context, game_path, names):
    names = names.split(", ") if ", " in names and "(USA, Europe)" not in names else [names]
    game = {"system": game_path.split("/")[0], "title": names[-1], "names": names, "path": Path(game_path)}
    em_context["game"] = game
    em_context["saved"] = emumovies.fetch_emumovies(
        game, em_context["media_root"], em_context["connection"], logger(em_context)
    )


@when(parsers.parse('EmuMovies media is fetched for "{game_path}" named "{names}"'))
def media_fetched(em_context, game_path, names):
    fetch(em_context, game_path, names)


@when(parsers.parse('EmuMovies is reconnected and media is fetched for "{game_path}" named "{names}"'))
def reconnected_and_fetched(em_context, game_path, names):
    em_context["connection"].close()
    open_server(em_context)
    fetch(em_context, game_path, names)


@when(parsers.parse('the cached listings are a day old and media is fetched for "{game_path}" named "{names}"'))
def stale_and_fetched(em_context, game_path, names):
    em_context["connection"].close()
    listings = json.loads(em_context["cache"].read_text())
    for cached in listings.values():
        cached["listed"] -= emumovies.LISTING_TTL_SECONDS + 1
    em_context["cache"].write_text(json.dumps(listings))
    open_server(em_context)
    fetch(em_context, game_path, names)


@when("EmuMovies is connected to")
def connected(em_context):
    em_context["connection"] = emumovies.connect(logger(em_context))


@when("the EmuMovies connection is closed")
def connection_closed(em_context):
    em_context["connection"].close()


@then(parsers.parse('EmuMovies should have saved "{media}"'))
def saved_media(em_context, media):
    assert sorted(em_context["saved"]) == sorted(media.split(", "))


@then("EmuMovies should have saved nothing")
def saved_nothing(em_context):
    assert em_context["saved"] == []


def saved_file(em_context, media_type):
    game = em_context["game"]
    for suffix in ESDE_MEDIA_TYPES[media_type]:
        path = esde_media_path(em_context["media_root"], game["system"], game["path"], media_type, suffix)
        if path.exists():
            return path
    raise AssertionError(f"no {media_type} saved")


@then(parsers.parse('the ES-DE "{media_type}" file should have come from "{source}"'))
def file_from(em_context, media_type, source):
    assert saved_file(em_context, media_type).read_bytes().decode().startswith(f"Official/{source}")


@then(parsers.parse('the EmuMovies log should mention "{text}"'))
def log_mentions(em_context, text):
    assert any(text in message for message in em_context["log"])


@then("no partly downloaded files should be left")
def no_partial_files(em_context):
    assert not list(em_context["media_root"].rglob(".emumovies-*"))


@then("the server should have been asked for each folder once")
def listed_once(em_context):
    assert set(em_context["server"].listed.values()) == {1}


@then("the server should have been asked for each folder twice")
def listed_twice(em_context):
    assert set(em_context["server"].listed.values()) == {2}


@then("deleting, uploading, renaming and making folders on EmuMovies should be refused")
def changes_refused(em_context):
    ftp = em_context["connection"].ftp
    attempts = [
        lambda: ftp.delete("Official/Video Snaps (HQ)/x.mp4"),
        lambda: ftp.storbinary("STOR x.mp4", None),
        lambda: ftp.rename("a", "b"),
        lambda: ftp.mkd("new"),
        lambda: ftp.rmd("Official"),
        lambda: ftp.sendcmd("DELE x.mp4"),
    ]
    for attempt in attempts:
        with pytest.raises(PermissionError):
            attempt()


@then("a download command other than RETR should be refused")
def only_retr(em_context):
    with pytest.raises(PermissionError):
        em_context["connection"].ftp.retrbinary("STOR x.mp4", lambda data: None)


@then("nothing on the EmuMovies server should have changed")
def server_unchanged(em_context):
    assert em_context["server"].changes == []


@then("there should be no EmuMovies connection")
def no_connection(em_context):
    assert em_context["connection"] is None


@then(parsers.parse('there should be no EmuMovies connection and the log should say "{text}"'))
def no_connection_logged(em_context, text):
    assert em_context["connection"] is None
    log_mentions(em_context, text)


@then("the EmuMovies connection should be encrypted")
def connection_encrypted(em_context):
    assert isinstance(em_context["connection"].ftp._ftp, FakeFTPTLS)


@then("the EmuMovies connection should be plain FTP")
def connection_plain(em_context):
    assert type(em_context["connection"].ftp._ftp) is FakeFTP


@then("the EmuMovies connection should be to the backup server")
def connected_to_backup(em_context):
    assert em_context["connection"].ftp._ftp.host == "backup.example"


@then("the EmuMovies listings should be saved")
def listings_saved(em_context):
    assert json.loads(em_context["cache"].read_text())


@then("the EmuMovies listing cache should exist")
def listing_cache_exists(em_context):
    assert em_context["cache"].is_file()
