"""
Step implementations for media naming and Steam ROM Manager
"""

import json
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import media, settings
from modules.media import (
    esde_media_name,
    esde_media_path,
    media_coverage,
    steam_artwork_path,
    steam_artwork_root,
)
from modules.srm import BACKUP_SUFFIX, configure_srm


@pytest.fixture
def steam_context(tmp_path):
    return {"tmp": tmp_path, "log": [], "srm_config": tmp_path / "userConfigurations.json"}


scenarios("../features/steam.feature")


@given(parsers.parse('a game folder "{folder}" and a game file "{file}"'))
def game_folder_and_file(steam_context, folder, file):
    (steam_context["tmp"] / folder).mkdir(parents=True)
    (steam_context["tmp"] / file).parent.mkdir(parents=True)
    (steam_context["tmp"] / file).write_bytes(b"rom")


@then(parsers.parse('the ES-DE media name for "{game}" should be "{name}"'))
def esde_name_is(steam_context, game, name):
    assert esde_media_name(steam_context["tmp"] / game) == name


@then(parsers.parse('the Steam image for "{game}" should be named "{name}"'))
def steam_name_is(steam_context, game, name):
    path = steam_artwork_path("art", "psx", steam_context["tmp"] / game, "tall", ".png")
    assert path.name == name


@given(parsers.parse('the games "{games}"'))
def games_listed(steam_context, games):
    steam_context["games"] = [
        (game.split("/")[0], steam_context["tmp"] / "roms" / game) for game in games.split(", ")
    ]


def add_media(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"media")


@given(parsers.re(r'"(?P<game>[^"]+)" has ES-DE "(?P<types>[^"]+)"(?: and Steam "(?P<kinds>[^"]+)")?'))
def game_has_media(steam_context, game, types, kinds):
    system = game.split("/")[0]
    suffixes = {"videos": ".mp4", "manuals": ".pdf"}
    for media_type in types.split(", "):
        add_media(
            esde_media_path(
                steam_context["tmp"] / "media", system, game, media_type,
                suffixes.get(media_type, ".jpg"),
            )
        )
    for kind in (kinds or "").split(", ") if kinds else []:
        add_media(steam_artwork_path(steam_context["tmp"] / "steam", system, game, kind, ".png"))


@when("media coverage is measured")
def coverage_measured(steam_context):
    steam_context["coverage"] = media_coverage(
        steam_context["games"], steam_context["tmp"] / "media", steam_context["tmp"] / "steam"
    )


@then(
    parsers.parse(
        'coverage should count {total:d} games with {covers:d} "covers", {videos:d} "videos", '
        '{manuals:d} "manuals" and {tall:d} "steam_tall"'
    )
)
def coverage_counts(steam_context, total, covers, videos, manuals, tall):
    coverage = steam_context["coverage"]
    assert coverage["total"] == total
    by_type = coverage["by_type"]
    assert (by_type["covers"], by_type["videos"], by_type["manuals"], by_type["steam_tall"]) == (
        covers, videos, manuals, tall,
    )
    assert by_type["screenshots"] == 0


@then(parsers.parse('"{system}" should have {games:d} games with {covers:d} "covers"'))
def system_coverage(steam_context, system, games, covers):
    row = steam_context["coverage"]["by_system"][system]
    assert (row["games"], row["covers"]) == (games, covers)


@given(parsers.parse('ES-DE\'s media folder is "{folder}"'))
def esde_media_folder(steam_context, monkeypatch, folder):
    monkeypatch.setitem(settings.current, "steam_artwork_dir", "")
    monkeypatch.setattr(media.esde, "media_root", lambda: steam_context["tmp"] / folder)


@when(parsers.parse('the Steam artwork folder is set to "{folder}"'))
def steam_folder_set(monkeypatch, folder):
    monkeypatch.setitem(settings.current, "steam_artwork_dir", folder)


@then(parsers.parse('the Steam artwork folder should be "{folder}" expanded'))
def steam_folder_expanded(folder):
    assert steam_artwork_root() == Path(folder).expanduser()


@then(parsers.parse('the Steam artwork folder should be "{folder}"'))
def steam_folder_is(steam_context, folder):
    assert steam_artwork_root() == steam_context["tmp"] / folder


@given("Steam ROM Manager parsers")
def srm_parsers(steam_context, datatable):
    header, *rows = datatable
    parsers_config = []
    for row in rows:
        values = dict(zip(header, row))
        parsers_config.append(
            {
                "configTitle": values["configTitle"],
                "romDirectory": values["romDirectory"],
                "parserInputs": {"glob": values["glob"].replace("\\|", "|")},
                "localImages": {"tall": values["tall"], "long": "", "hero": "", "logo": "", "icon": ""},
            }
        )
    steam_context["original"] = json.dumps(parsers_config)
    steam_context["srm_config"].write_text(steam_context["original"])


@given(parsers.parse('the Steam artwork folder is "{folder}"'))
def steam_artwork_folder(steam_context, folder):
    steam_context["steam_root"] = steam_context["tmp"] / folder


@given("Steam ROM Manager's parsers are missing")
def srm_missing(steam_context):
    steam_context["steam_root"] = steam_context["tmp"] / "art"


@given("Steam ROM Manager's parsers are broken")
def srm_broken(steam_context):
    steam_context["steam_root"] = steam_context["tmp"] / "art"
    steam_context["srm_config"].write_text("{not json")


@when("Steam ROM Manager is set up")
def srm_set_up(steam_context):
    steam_context["result"] = configure_srm(
        steam_context["steam_root"],
        lambda message, level="INFO": steam_context["log"].append(message),
        steam_context["srm_config"],
    )


def parser_images(steam_context, title):
    for parser in json.loads(steam_context["srm_config"].read_text()):
        if parser["configTitle"] == title:
            return parser["localImages"]
    raise AssertionError(f"no parser {title}")


@then(parsers.parse('"{title}" should look for "{kind}" art in "{glob}"'))
def parser_looks_for(steam_context, title, kind, glob):
    root = steam_context["tmp"].as_posix()
    expected = glob if glob.startswith("/") else f"{root}/{glob}"
    assert parser_images(steam_context, title)[kind] == expected


@then(parsers.parse('"{title}" should have no local art'))
def parser_has_no_art(steam_context, title):
    assert not any(parser_images(steam_context, title).values())


@then(parsers.parse('the setup should report updating "{titles}"'))
def setup_updated(steam_context, titles):
    assert steam_context["result"]["updated"] == (titles.split(", ") if titles else [])


@then("the original parsers should be backed up")
def parsers_backed_up(steam_context):
    backup = Path(steam_context["result"]["backup"])
    assert backup.name == steam_context["srm_config"].name + BACKUP_SUFFIX
    assert backup.read_text() == steam_context["original"]


@then("the setup should fail")
def setup_failed(steam_context):
    assert "error" in steam_context["result"]


@then("the second setup should report no changes")
def second_setup_no_changes(steam_context):
    assert steam_context["result"]["updated"] == []
