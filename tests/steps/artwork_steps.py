"""
Step implementations for downloading images for ES-DE and Steam
"""

from pathlib import Path
from urllib.parse import quote

import pytest
import requests
from pytest_bdd import given, scenarios, then, when, parsers

from modules import settings

from modules.artwork import API_BASE, LIBRETRO_BASE, fetch_artwork
from modules.media import (
    ESDE_MEDIA_TYPES,
    STEAM_IMAGE_TYPES,
    esde_media_path,
    steam_artwork_path,
)

SGDB_GAME_ID = 42


class FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b""):
        self.status_code = status_code
        self.payload = payload
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture
def art_context(tmp_path, monkeypatch):
    context = {
        "tmp": tmp_path,
        "media_root": tmp_path / "downloaded_media",
        "steam_root": tmp_path / "steam-artwork",
        "requests": [],
        "log": [],
        "libretro": set(),
        "libretro_reachable": True,
        "sgdb_games": [],
        "sgdb_images": False,
        "sgdb_reachable": True,
        "image_suffix": ".png",
    }

    def fake_get(url, params=None, **kwargs):
        context["requests"].append((url, params or {}))

        if url.startswith(LIBRETRO_BASE):
            if not context["libretro_reachable"]:
                raise requests.ConnectionError("libretro down")
            found = url in context["libretro"]
            return FakeResponse(200 if found else 404, content=b"libretro image")

        if not context["sgdb_reachable"]:
            raise requests.ConnectionError("network down")
        if "/search/autocomplete/" in url:
            return FakeResponse(payload={"data": context["sgdb_games"]})
        if url.startswith(f"{API_BASE}/"):
            endpoint = url[len(API_BASE) + 1 :].split("/")[0]
            images = []
            if context["sgdb_images"]:
                dimensions = (params or {}).get("dimensions", "")
                images = [{"url": f"https://cdn.example/{endpoint}-{dimensions}{context['image_suffix']}"}]
            return FakeResponse(payload={"data": images})
        return FakeResponse(content=f"sgdb {url}".encode())

    monkeypatch.setattr("modules.artwork.requests.get", fake_get)
    monkeypatch.setitem(settings.current, "enable_libretro_thumbnails", True)
    monkeypatch.setitem(settings.current, "enable_steamgriddb", True)
    monkeypatch.setitem(settings.current, "steamgriddb_api", "test-key")
    return context


scenarios("../features/artwork.feature")


@given(parsers.parse('libretro has "{kinds}" for "{name}" in "{folder}"'))
def libretro_has(art_context, kinds, name, folder):
    for kind in kinds.split(", "):
        art_context["libretro"].add(f"{LIBRETRO_BASE}/{quote(folder)}/{kind}/{quote(name)}.png")


@given("libretro can't be reached")
def libretro_unreachable(art_context):
    art_context["libretro_reachable"] = False


# The switches below take art_context so they run after it turns both sources on
@given("libretro thumbnails are disabled")
def libretro_disabled(art_context, monkeypatch):
    monkeypatch.setitem(settings.current, "enable_libretro_thumbnails", False)


@given("SteamGridDB has every kind of image for its game")
def sgdb_has_everything(art_context):
    art_context["sgdb_games"] = [{"id": SGDB_GAME_ID}]
    art_context["sgdb_images"] = True


@given("SteamGridDB has every kind of image for its game as JPEG")
def sgdb_has_jpegs(art_context):
    sgdb_has_everything(art_context)
    art_context["image_suffix"] = ".jpg?v=2"


@given("SteamGridDB is disabled")
def sgdb_disabled(art_context, monkeypatch):
    monkeypatch.setitem(settings.current, "enable_steamgriddb", False)


@given("SteamGridDB has no API key")
def sgdb_no_key(art_context, monkeypatch):
    monkeypatch.setitem(settings.current, "steamgriddb_api", "")


@given("SteamGridDB finds no game")
def sgdb_no_game():
    pass


@given("SteamGridDB has no images for the game")
def sgdb_no_images(art_context):
    art_context["sgdb_games"] = [{"id": SGDB_GAME_ID}]


@given("SteamGridDB can't be reached")
def sgdb_unreachable(art_context):
    art_context["sgdb_reachable"] = False


@given(parsers.parse('"{game_path}" already has every image'))
def game_has_every_image(art_context, game_path):
    system = game_path.split("/")[0]
    for media_type in ESDE_MEDIA_TYPES:
        path = esde_media_path(art_context["media_root"], system, game_path, media_type, ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"existing")
    game_has_steam_artwork(art_context, game_path)


@given(parsers.parse('"{game_path}" already has its Steam artwork'))
def game_has_steam_artwork(art_context, game_path):
    system = game_path.split("/")[0]
    for kind in STEAM_IMAGE_TYPES:
        path = steam_artwork_path(art_context["steam_root"], system, game_path, kind, ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"existing")


@when(
    parsers.re(
        r'artwork is fetched for "(?P<game_path>[^"]+)" named "(?P<names>[^"]+)"'
        r'(?: from the DAT "(?P<dat_title>[^"]+)")?'
    )
)
def artwork_fetched(art_context, game_path, names, dat_title):
    names = names.split(", ")
    game = {
        "system": game_path.split("/")[0],
        "title": names[-1],
        "names": names,
        "dat_title": dat_title,
        "path": Path(game_path),
    }
    art_context["game"] = game
    art_context["saved"] = fetch_artwork(
        game,
        art_context["media_root"],
        art_context["steam_root"],
        lambda message, level="INFO": art_context["log"].append(message),
    )


@then(parsers.parse('the saved media should be "{media}"'))
def saved_media_are(art_context, media):
    assert sorted(art_context["saved"]) == sorted(media.split(", "))


@then("the saved media should be nothing")
def saved_media_nothing(art_context):
    assert art_context["saved"] == []


def esde_image(art_context, media_type, suffix=".png"):
    game = art_context["game"]
    return esde_media_path(
        art_context["media_root"], game["system"], game["path"], media_type, suffix
    )


@then(parsers.parse('the ES-DE "{media_type}" image should come from libretro'))
def esde_image_from_libretro(art_context, media_type):
    assert esde_image(art_context, media_type).read_bytes() == b"libretro image"


@then(parsers.parse('the ES-DE "{media_type}" image should come from SteamGridDB "{endpoint}"'))
def esde_image_from_sgdb(art_context, media_type, endpoint):
    assert f"/{endpoint}-".encode() in esde_image(art_context, media_type).read_bytes()


@then(
    parsers.parse(
        'the Steam "{kind}" image should come from SteamGridDB "{endpoint}" sized "{dimensions}"'
    )
)
def steam_image_from_sgdb(art_context, kind, endpoint, dimensions):
    game = art_context["game"]
    image = steam_artwork_path(art_context["steam_root"], game["system"], game["path"], kind, ".png")
    assert image.read_bytes() == f"sgdb https://cdn.example/{endpoint}-{dimensions}.png".encode()


@then(parsers.re(r'the Steam "(?P<kind>\w+)" image should be saved for "(?P<name>[^"]+)"(?: as "(?P<suffix>[^"]+)")?'))
def steam_image_saved(art_context, kind, name, suffix):
    system = art_context["game"]["system"]
    assert (art_context["steam_root"] / system / kind / f"{name}{suffix or '.png'}").is_file()


@then(parsers.parse('the ES-DE "{media_type}" image should be saved for "{name}"'))
def esde_image_saved(art_context, media_type, name):
    system = art_context["game"]["system"]
    assert (art_context["media_root"] / system / media_type / f"{name}.png").is_file()


@then(parsers.parse('the artwork log should mention "{text}"'))
def artwork_log_mentions(art_context, text):
    assert any(text in message for message in art_context["log"])


@then("libretro should not be asked")
def libretro_not_asked(art_context):
    assert not any(url.startswith(LIBRETRO_BASE) for url, _ in art_context["requests"])


@then("nothing should be requested")
def nothing_requested(art_context):
    assert art_context["requests"] == []
