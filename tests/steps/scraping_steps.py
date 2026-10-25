"""
Step implementations for scraping and artwork tests
"""

import pytest
import requests
from pytest_bdd import given, scenario, scenarios, then, when, parsers

from modules import artwork, scraper, settings


@pytest.fixture
def scrape_context(tmp_path):
    return {"tmp": tmp_path, "log": [], "requests": []}


def record_log(scrape_context):
    return lambda message, level="INFO": scrape_context["log"].append(message)


@scenario("../features/scraping.feature", "Missing Skyscraper is reported instead of crashing")
def test_missing_skyscraper_reported():
    pass


@scenario(
    "../features/scraping.feature",
    "Skyscraper gathers from ScreenScraper and writes ES-DE game data",
)
def test_skyscraper_commands():
    pass






scenarios("../features/scraping.feature")


@given("ScreenScraper is disabled")
def screenscraper_disabled(monkeypatch):
    monkeypatch.setitem(settings.current, "enable_screenscraper", False)


@given("no ScreenScraper credentials")
def no_screenscraper_credentials(monkeypatch):
    monkeypatch.setitem(settings.current, "screenscraper_user", "")
    monkeypatch.setitem(settings.current, "screenscraper_password", "")


# Examples tables turn "\n" into a real newline, so the output may span lines
@given(
    parsers.re(
        r'(?s)Skyscraper is installed and exits with (?P<code>\d+)(?: printing "(?P<output>.*)")?'
    )
)
def skyscraper_installed(scrape_context, monkeypatch, code, output):
    install_fake_skyscraper(scrape_context, monkeypatch, int(code), (output or "").split("\n"))


class FakeSkyscraper:
    """Stands in for subprocess.Popen: prints lines, then exits with a code."""

    def __init__(self, scrape_context, code, lines, command, **kwargs):
        scrape_context["commands"].append(command)
        scrape_context["popen_kwargs"] = kwargs
        self.scrape_context = scrape_context
        self.code = code
        self.stdout = iter(line + "\n" for line in lines)

    def terminate(self):
        self.scrape_context["terminated"] = True

    def wait(self):
        return self.code


def install_fake_skyscraper(scrape_context, monkeypatch, code, lines):
    scrape_context["commands"] = []
    monkeypatch.setitem(settings.current, "enable_screenscraper", True)
    monkeypatch.setattr("modules.scraper.shutil.which", lambda name: "/usr/bin/Skyscraper")
    monkeypatch.setattr(
        "modules.scraper.subprocess.Popen",
        lambda command, **kwargs: FakeSkyscraper(scrape_context, code, lines, command, **kwargs),
    )
    monkeypatch.setitem(settings.current, "esde_home", str(scrape_context["tmp"] / "ES-DE"))


@given("Skyscraper is not installed")
def skyscraper_not_installed(monkeypatch):
    monkeypatch.setitem(settings.current, "enable_screenscraper", True)
    monkeypatch.setattr("modules.scraper.shutil.which", lambda name: None)


@given(parsers.parse('ScreenScraper credentials "{user}" and "{password}"'))
def screenscraper_credentials(monkeypatch, user, password):
    monkeypatch.setitem(settings.current, "screenscraper_user", user)
    monkeypatch.setitem(settings.current, "screenscraper_password", password)


@given("ES-DE lives in a temporary folder")
def esde_in_temp_folder(scrape_context, monkeypatch):
    monkeypatch.setitem(settings.current, "esde_home", str(scrape_context["tmp"] / "ES-DE"))


@when(parsers.parse('game data is scraped for "{system}"'))
def scrape_system(scrape_context, system):
    scrape_context["result"] = scraper.run_skyscraper(
        system, record_log(scrape_context), scrape_context["tmp"]
    )


@when(parsers.parse('the Skyscraper commands are built for "{system}"'))
def build_commands(scrape_context, system):
    scrape_context["gather"], scrape_context["generate"] = scraper.skyscraper_commands(
        system, scrape_context["tmp"] / "roms"
    )


@then("scraping should report success")
def scraping_succeeded(scrape_context):
    assert scrape_context["result"] is True


@then("scraping should report failure")
def scraping_failed(scrape_context):
    assert scrape_context["result"] is False


@then("Skyscraper should have run the gather then the generate command")
def ran_gather_then_generate(scrape_context):
    gather, generate = scrape_context["commands"]
    assert gather[0] == "/usr/bin/Skyscraper"
    assert "-s" in gather and "-s" not in generate
    assert option(generate, "-i") == str(scrape_context["tmp"] / "snes")


@then("Skyscraper should have run only the gather command")
def ran_only_gather(scrape_context):
    assert len(scrape_context["commands"]) == 1
    assert "-s" in scrape_context["commands"][0]


@then("the gather command should not pass credentials")
def gather_without_credentials(scrape_context):
    assert "-u" not in scrape_context["gather"]


@then("scraping should report it can't run")
def scraping_cannot_run(scrape_context):
    assert scrape_context["result"] is None


@then(parsers.parse('the scraping log should mention "{text}"'))
def scraping_log_mentions(scrape_context, text):
    assert any(text in message for message in scrape_context["log"])


def option(command, flag):
    return command[command.index(flag) + 1]


@then(
    parsers.parse(
        'the gather command should scrape platform "{platform}" with credentials "{credentials}"'
    )
)
def gather_command(scrape_context, platform, credentials):
    gather = scrape_context["gather"]
    assert option(gather, "-p") == platform
    assert option(gather, "-s") == "screenscraper"
    assert option(gather, "-u") == credentials
    # Every media type ES-DE can show, not just covers and screenshots
    assert set(option(gather, "--flags").split(",")) >= {"backcovers", "fanarts", "manuals", "videos"}


@then(parsers.parse('the generate command should write the ES-DE gamelist and media for "{system}"'))
def generate_command(scrape_context, system):
    generate = scrape_context["generate"]
    esde_home = scrape_context["tmp"] / "ES-DE"
    assert "-s" not in generate
    assert option(generate, "-f") == "esde"
    assert "videos" in option(generate, "--flags").split(",")
    assert option(generate, "-g") == str(esde_home / "gamelists" / system)
    assert option(generate, "-o") == str(esde_home / "downloaded_media" / system)
    assert option(generate, "-i") == str(scrape_context["tmp"] / "roms" / system)


@given(parsers.parse('Skyscraper is installed and prints "{lines}"'))
def skyscraper_prints(scrape_context, monkeypatch, lines):
    install_fake_skyscraper(scrape_context, monkeypatch, 0, lines.split(" | "))
    monkeypatch.setitem(settings.current, "esde_home", str(scrape_context["tmp"] / "ES-DE"))


@when(parsers.parse('game data is scraped for "{system}" while watching its output'))
def scrape_watching(scrape_context, system):
    scrape_context["output"] = []
    scrape_context["result"] = scraper.run_skyscraper(
        system, record_log(scrape_context), scrape_context["tmp"],
        on_output=scrape_context["output"].append,
    )


@when(parsers.parse('game data is scraped for "{system}" and stopped after "{line}"'))
def scrape_and_stop(scrape_context, system, line):
    scrape_context["output"] = []
    scrape_context["result"] = scraper.run_skyscraper(
        system, record_log(scrape_context), scrape_context["tmp"],
        on_output=scrape_context["output"].append,
        should_stop=lambda: line in scrape_context["output"],
    )


@then(parsers.parse('the output seen should be "{lines}"'))
def output_seen(scrape_context, lines):
    assert scrape_context["output"] == lines.split(" | ")


@then("Skyscraper should get no input")
def skyscraper_no_input(scrape_context):
    assert scrape_context["popen_kwargs"]["stdin"] is scraper.subprocess.DEVNULL


@then("Skyscraper should have been stopped")
def skyscraper_stopped(scrape_context):
    assert scrape_context["terminated"] is True


@then(parsers.parse('the gather command should scrape platform "{platform}"'))
def gather_platform(scrape_context, platform):
    assert option(scrape_context["gather"], "-p") == platform
