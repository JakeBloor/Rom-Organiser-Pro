"""
Step implementations for the organise API used by the web page
"""

import json
import time

import pytest
from pytest_bdd import given, scenario, scenarios, then, when, parsers

import app as rom_app
from modules import esde, settings

RUN_TIMEOUT_SECONDS = 10


@pytest.fixture
def web_context():
    return {}


@scenario(
    "../features/web.feature",
    "A dry run started from the page reports progress and moves nothing",
)
def test_dry_run_through_api():
    pass


@scenario("../features/web.feature", "A run with a missing import folder is rejected")
def test_missing_import_folder_rejected():
    pass


scenarios("../features/web.feature")


@given(parsers.parse('an import folder with "{filename}" and an empty ROM folder'))
def import_and_rom_folders(web_context, tmp_path, filename):
    import_dir = tmp_path / "import"
    import_dir.mkdir()
    rom = import_dir / filename
    rom.write_bytes(b"rom data")
    rom_root = tmp_path / "roms"
    rom_root.mkdir()
    web_context.update(import_dir=import_dir, rom=rom, rom_root=rom_root)


@given(parsers.parse('the import folder also has "{filename}"'))
def import_folder_also_has(web_context, filename):
    (web_context["import_dir"] / filename).write_bytes(b"more rom data")


def stub_scraping(web_context, monkeypatch, scrape_result, cover_downloaded=True):
    web_context["scraped"] = []

    def fake_scrape(system, logger, rom_root):
        web_context["scraped"].append(system)
        return scrape_result

    monkeypatch.setattr(rom_app, "run_skyscraper", fake_scrape)
    monkeypatch.setattr(
        rom_app,
        "fetch_artwork",
        lambda *args: ["covers", "steam_tall"] if cover_downloaded else [],
    )


@given("scraping and cover downloads are stubbed")
def scraping_stubbed(web_context, monkeypatch):
    stub_scraping(web_context, monkeypatch, True)


@given("scraping is stubbed and no covers are downloaded")
def no_covers_downloaded(web_context, monkeypatch):
    stub_scraping(web_context, monkeypatch, True, cover_downloaded=False)


@given("ES-DE keeps its media in a temporary folder")
def esde_media_in_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(esde, "media_root", lambda: tmp_path / "ES-DE" / "downloaded_media")
    monkeypatch.setitem(settings.current, "steam_artwork_dir", str(tmp_path / "steam-artwork"))


@given("Steam ROM Manager has a DuckStation parser")
def srm_has_parser(monkeypatch, tmp_path):
    config = tmp_path / "userConfigurations.json"
    config.write_text(
        json.dumps(
            [
                {
                    "configTitle": "Sony PlayStation - DuckStation",
                    "romDirectory": "${romsdirglobal}/psx",
                    "parserInputs": {"glob": "**/${title}@(.chd)"},
                    "localImages": {},
                }
            ]
        )
    )
    monkeypatch.setitem(settings.current, "srm_config", str(config))
    monkeypatch.setitem(settings.current, "steam_artwork_dir", str(tmp_path / "steam-artwork"))


@given("Steam ROM Manager isn't installed")
def srm_not_installed(monkeypatch, tmp_path):
    monkeypatch.setitem(settings.current, "srm_config", str(tmp_path / "missing" / "userConfigurations.json"))


@given("there is no DAT folder yet")
def no_dat_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(rom_app, "DAT_DIR", tmp_path / "dats")


@given("scraping can't run and cover downloads are stubbed")
def scraping_cannot_run(web_context, monkeypatch):
    stub_scraping(web_context, monkeypatch, None)


@given(parsers.parse('organising fails with "{message}"'))
def organising_fails(monkeypatch, message):
    def failing_process_roms(*args, **kwargs):
        raise RuntimeError(message)

    monkeypatch.setattr(rom_app, "process_roms", failing_process_roms)


@given("an organise run is already in progress")
def run_in_progress():
    rom_app.organise_lock.acquire()
    yield
    rom_app.organise_lock.release()


@given(parsers.parse('the DAT folder holds "{name}"'))
def dat_folder_holds(web_context, monkeypatch, tmp_path, name):
    dat_dir = tmp_path / "dats"
    dat_dir.mkdir()
    (dat_dir / name).write_text("clrmamepro ()")
    monkeypatch.setattr(rom_app, "DAT_DIR", dat_dir)


class UnreadableFolder:
    def exists(self):
        raise PermissionError("permission denied")


@given("the DAT folder can't be read")
def dat_folder_unreadable(monkeypatch):
    monkeypatch.setattr(rom_app, "DAT_DIR", UnreadableFolder())


@given(parsers.parse('a ROM folder holding "{first}" and "{second}"'))
def rom_folder_holding(web_context, tmp_path, first, second):
    rom_root = tmp_path / "library"
    for relative_path in (first, second):
        path = rom_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"rom data")
    web_context["rom_root"] = rom_root


@given("ES-DE's ROM folder is that folder")
def esde_rom_folder_is(web_context, monkeypatch):
    monkeypatch.setattr(esde, "rom_root", lambda: web_context["rom_root"])


@given("ES-DE's ROM folder exists")
def esde_rom_folder_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(esde, "rom_root", lambda: tmp_path)


@given(parsers.parse('scanning fails with "{message}"'))
def scanning_fails(monkeypatch, message):
    def failing_scan(rom_root, systems=None):
        raise OSError(message)

    monkeypatch.setattr(rom_app, "update_detection_stats", failing_scan)


@given("DAT fetch and load functions are stubbed")
def dat_functions_stubbed(monkeypatch):
    monkeypatch.setattr(rom_app, "fetch_latest_dats", lambda logger: {})
    monkeypatch.setattr(rom_app, "load_dat_files", lambda logger: None)


@given(parsers.parse('DAT loading fails with "{message}"'))
def dat_loading_fails(monkeypatch, message):
    def failing_fetch(logger):
        raise RuntimeError(message)

    monkeypatch.setattr(rom_app, "fetch_latest_dats", failing_fetch)


def start_run(client, input_path, rom_root, dry_run=True):
    return client.post(
        "/api/organise",
        json={"input_path": str(input_path), "rom_root": str(rom_root), "dry_run": dry_run},
    )


@when("a dry run is started through the API")
def start_dry_run(client, web_context):
    web_context["response"] = start_run(
        client, web_context["import_dir"], web_context["rom_root"]
    )
    assert web_context["response"].status_code == 202


@when("a real run is started through the API")
def start_real_run(client, web_context):
    web_context["response"] = start_run(
        client, web_context["import_dir"], web_context["rom_root"], dry_run=False
    )
    assert web_context["response"].status_code == 202


@when("a dry run is requested through the API")
def request_dry_run(client, web_context):
    web_context["response"] = start_run(
        client, web_context["import_dir"], web_context["rom_root"]
    )


@when("a run is started for a missing ROM folder")
def start_missing_rom_folder_run(client, web_context):
    web_context["response"] = start_run(
        client, web_context["import_dir"], web_context["rom_root"] / "missing"
    )


@when("the ROM folder is scanned through the API")
def scan_through_api(client, web_context):
    web_context["scan"] = client.post(
        "/api/scan-games", json={"rom_root": str(web_context["rom_root"])}
    )


@when(parsers.parse('the ROM folder\'s "{systems}" games are scanned through the API'))
def scan_systems_through_api(client, web_context, systems):
    web_context["scan"] = client.post(
        "/api/scan-games",
        json={"rom_root": str(web_context["rom_root"]), "systems": systems.split(", ")},
    )


@when(parsers.parse('the ROM folder is scanned through the API with systems "{systems}"'))
def scan_bad_systems_through_api(client, web_context, systems):
    web_context["scan"] = client.post(
        "/api/scan-games", json={"rom_root": str(web_context["rom_root"]), "systems": systems}
    )


@when("the ROM folder's systems are listed through the API")
def list_systems_through_api(client, web_context):
    web_context["systems"] = client.get(
        "/api/systems", query_string={"rom_root": str(web_context["rom_root"])}
    )


@when("the default ROM folder's systems are listed through the API")
def list_default_systems_through_api(client, web_context):
    web_context["systems"] = client.get("/api/systems")


@when("a missing ROM folder's systems are listed through the API")
def list_missing_systems_through_api(client, web_context, tmp_path):
    web_context["systems"] = client.get(
        "/api/systems", query_string={"rom_root": str(tmp_path / "missing")}
    )


@when("the default ROM folder is scanned through the API")
def scan_default_through_api(client, web_context):
    web_context["scan"] = client.post("/api/scan-games", json={})


@when("a missing ROM folder is scanned through the API")
def scan_missing_through_api(client, web_context, tmp_path):
    web_context["scan"] = client.post(
        "/api/scan-games", json={"emudeck_path": str(tmp_path / "missing")}
    )


@when("the status API is requested")
def status_api_requested(client, web_context):
    web_context["api_status"] = client.get("/api/status")


@when("Steam ROM Manager is set up through the API")
def srm_setup_through_api(client, web_context):
    web_context["srm"] = client.post("/api/steam-rom-manager")


@when("the app starts up")
def app_starts_up():
    rom_app.initialize_dat_files()


@when("a run is started for a missing import folder")
def start_missing_folder_run(client, web_context):
    web_context["response"] = start_run(
        client, web_context["import_dir"] / "missing", web_context["rom_root"]
    )


@when("the run finishes")
def run_finishes(client, web_context):
    deadline = time.time() + RUN_TIMEOUT_SECONDS
    while time.time() < deadline:
        status = client.get("/status").get_json()
        if not status["running"]:
            web_context["status"] = status
            return
        time.sleep(0.05)
    pytest.fail("organise run did not finish")


@then("the status should show 1 game organised in a dry run")
def status_shows_dry_run(web_context):
    status = web_context["status"]
    assert status["phase"] == "done"
    assert status["dry_run"] is True
    assert status["roms_processed"] == 1
    assert status["progress"] == 100


@then(parsers.re(r"the status should show the run finished with (?P<covers>\d+) covers? downloaded"))
def status_shows_real_run(web_context, covers):
    status = web_context["status"]
    assert status["phase"] == "done"
    assert status["dry_run"] is False
    assert status["artwork_downloads"] == int(covers)


@then(parsers.parse('"{system}" should have been scraped'))
def system_scraped(web_context, system):
    assert web_context["scraped"] == [system]


@then(parsers.parse('only "{system}" should have been scraped'))
def only_system_scraped(web_context, system):
    assert web_context["scraped"] == [system]


@then("nothing should have been scraped")
def nothing_scraped(web_context):
    assert web_context["scraped"] == []


@then(parsers.parse('the ROM folder should now hold "{relative_path}"'))
def rom_folder_now_holds(web_context, relative_path):
    assert (web_context["rom_root"] / relative_path).is_file()


@then(parsers.parse('the library should count {count:d} game for "{system}"'))
def library_counts(client, count, system):
    detection = client.get("/api/status").get_json()["detection"]
    assert detection["games_by_system"] == {system: count}


@then(parsers.parse('the status phase should be "{phase}"'))
def status_phase_is(web_context, phase):
    assert web_context["status"]["phase"] == phase


@then("another run can be started")
def another_run_can_start(client, web_context, monkeypatch):
    monkeypatch.undo()
    web_context["response"] = start_run(
        client, web_context["import_dir"], web_context["rom_root"]
    )
    assert web_context["response"].status_code == 202
    run_finishes(client, web_context)


@then("the API should refuse it as already running")
def api_refuses_running(web_context):
    assert web_context["response"].status_code == 409
    assert "already in progress" in web_context["response"].get_json()["error"]


@then(parsers.parse('the status API should list "{name}" and the API connections'))
def status_api_lists(web_context, name):
    data = web_context["api_status"].get_json()
    assert [dat["name"] for dat in data["dats"]["files"]] == [name]
    assert data["dats"]["total_files"] == 1
    assert set(data["apis"]) == {"steamgriddb", "screenscraper"}
    assert data["detection"]["total_games"] == 0
    assert data["detection"]["last_scan"]


@then("the status API should list no DAT files")
def status_api_no_dats(web_context):
    assert web_context["api_status"].get_json()["dats"]["total_files"] == 0


@then(parsers.parse('the status API should fail with "{text}"'))
def status_api_fails(web_context, text):
    assert web_context["api_status"].status_code == 500
    assert text in web_context["api_status"].get_json()["error"]


@then(parsers.parse("the scan should find {games:d} games across {systems:d} systems"))
def scan_finds(web_context, games, systems):
    data = web_context["scan"].get_json()
    assert data["success"] is True
    assert (data["total_games"], data["systems_detected"]) == (games, systems)


@then(parsers.parse('the scan and status API should say only "{systems}" was scanned'))
def scan_says_only(web_context, systems):
    expected = systems.split(", ")
    assert web_context["scan"].get_json()["scanned_systems"] == expected
    assert web_context["api_status"].get_json()["detection"]["scanned_systems"] == expected


@then("the scan should say all systems were scanned")
def scan_says_all(web_context):
    assert web_context["scan"].get_json()["scanned_systems"] is None


@then(parsers.parse('the API should list the systems "{systems}"'))
def api_lists_systems(web_context, systems):
    assert web_context["systems"].get_json()["systems"] == systems.split(", ")


@then(parsers.parse('listing the systems should fail with "{text}"'))
def listing_systems_fails(web_context, text):
    assert web_context["systems"].status_code == 404
    assert text in web_context["systems"].get_json()["error"]


@then(parsers.parse('the scan should fail with status {code:d} and "{text}"'))
def scan_fails(web_context, code, text):
    assert web_context["scan"].status_code == code
    data = web_context["scan"].get_json()
    assert data["success"] is False
    assert text in data["error"]


@then(parsers.parse("the run report should count {organised:d} organised and {unsorted:d} unsorted"))
def report_counts(web_context, organised, unsorted):
    outcomes = web_context["status"]["report"]["outcomes"]
    assert (outcomes["Organised"], outcomes["Unsorted"]) == (organised, unsorted)
    assert set(outcomes) == {"Organised", "Unsorted", "Skipped", "Duplicates"}


@then(parsers.parse('the run report should show {count:d} game for "{system}"'))
def report_by_system(web_context, count, system):
    assert web_context["status"]["report"]["by_system"] == {system: count}


@then(parsers.parse('the run report should list "{name}" as unsorted'))
def report_unsorted(web_context, name):
    assert web_context["status"]["report"]["unsorted_files"] == [name]


@then("the run report should have no media coverage")
def report_no_media(web_context):
    report = web_context["status"]["report"]
    assert report["dry_run"] is True
    assert report["media"] is None


@then(parsers.parse("the run report should cover {count:d} game"))
def report_covers(web_context, count):
    media = web_context["status"]["report"]["media"]
    assert media["total"] == count
    assert "steam_tall" in media["by_type"]


@then(parsers.parse('the status should count 1 "{first}" and 1 "{second}" download'))
def status_media_downloads(web_context, first, second):
    assert web_context["status"]["media_downloads"] == {first: 1, second: 1}


@then(parsers.parse("the scan should report media coverage for {count:d} games"))
def scan_reports_media(web_context, count):
    media = web_context["scan"].get_json()["media"]
    assert media["total"] == count
    assert set(media["by_system"]) == {"snes", "gb"}


@then(parsers.parse("the API should report {count:d} Steam ROM Manager parser updated"))
def srm_api_updated(web_context, count):
    assert web_context["srm"].status_code == 200
    assert len(web_context["srm"].get_json()["updated"]) == count


@then(parsers.parse("the Steam ROM Manager setup should fail with status {code:d}"))
def srm_api_failed(web_context, code):
    assert web_context["srm"].status_code == code
    assert "error" in web_context["srm"].get_json()


@then(parsers.parse('the startup log should mention "{text}"'))
def startup_log_mentions(text):
    assert any(text in message for message in rom_app.app_logger.get_messages())


@then(parsers.parse('the status log should mention "{text}"'))
def status_log_mentions(web_context, text):
    assert any(text in line for line in web_context["status"]["log"])


@then("the imported ROM should still be in the import folder")
def rom_still_imported(web_context):
    assert web_context["rom"].exists()
    assert list(web_context["rom_root"].iterdir()) == []


@then(parsers.parse('the API should reject it with "{text}"'))
def api_rejects(web_context, text):
    assert web_context["response"].status_code == 400
    assert text in web_context["response"].get_json()["error"]


@given(parsers.parse('the SteamGridDB API key "{key}" is saved'))
def web_api_key_saved(key):
    assert settings.save({"steamgriddb_api": key}) == {}


@given("settings.json can't be read")
def settings_unreadable():
    settings.SETTINGS_FILE.write_text("{not json")
    settings.load()


@when("the Settings page is opened")
def settings_page_opened(client, web_context):
    web_context["page"] = client.get("/settings")
    web_context["settings"] = client.get("/api/settings")


@when(parsers.parse('the settings are saved through the API with "{key}" set to "{value}"'))
def settings_saved_through_api(client, web_context, key, value):
    web_context["settings"] = client.post("/api/settings", json={key: value})


@when("the settings are saved through the API with a body that isn't an object")
def settings_saved_without_object(client, web_context):
    web_context["settings"] = client.post("/api/settings", json=["port"])


@when("the settings are saved through the API with a disk that's full")
def settings_saved_to_full_disk(client, web_context, monkeypatch):
    def failing_replace(source, destination):
        raise OSError("disk full")

    monkeypatch.setattr("modules.settings.os.replace", failing_replace)
    web_context["settings"] = client.post("/api/settings", json={"port": 9000})


@then(parsers.parse('the page should show "{first}" and "{second}"'))
def page_shows(web_context, first, second):
    page = web_context["page"].get_data(as_text=True)
    assert web_context["page"].status_code == 200
    assert first in page and second in page


@then(parsers.parse('the page should not contain "{text}"'))
def page_hides(web_context, text):
    assert text not in web_context["page"].get_data(as_text=True)


@then(parsers.parse('the settings API should show "{key}" as set without its value'))
def settings_api_hides_secret(web_context, key):
    assert web_context["settings"].get_json()["settings"][key] is True


@then("the settings API should report the save")
def settings_api_saved(web_context):
    data = web_context["settings"].get_json()
    assert data["saved"] is True
    assert data["restart_needed"] is False


@then("the status API should show SteamGridDB as configured")
def status_shows_steamgriddb(web_context):
    assert web_context["api_status"].get_json()["apis"]["steamgriddb"]["configured"] is True


@then("the settings API should say a restart is needed")
def settings_api_restart(web_context):
    assert web_context["settings"].get_json()["restart_needed"] is True


@then(parsers.parse('the settings API should refuse it with status {code:d} and "{message}"'))
def settings_api_refuses(web_context, code, message):
    assert web_context["settings"].status_code == code
    assert any(message in text for text in web_context["settings"].get_json()["errors"].values())
