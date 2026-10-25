"""
Step implementations for remembering what's known about files in the ROM folder
"""

import os

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules.cache import FileCache


@pytest.fixture
def cache_context(tmp_path):
    cache_file = tmp_path / "cache" / "files.json"
    return {"root": tmp_path / "roms", "file": cache_file, "cache": FileCache(cache_file)}


scenarios("../features/cache.feature")


def rom(cache_context, relative_path):
    return cache_context["root"] / relative_path


@given(parsers.re(r'a cached file "(?P<name>[^"]+)" with checksum "(?P<md5>[^"]+)"(?P<organised> that was organised)?'))
def cached_file(cache_context, name, md5, organised):
    path = rom(cache_context, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"rom {name}".encode())
    fields = {"md5": md5, "identity": md5}
    if organised:
        fields["outcome"] = "organised"
    cache_context["cache"].remember(path, **fields)


@given(parsers.parse("the cache file contains '{contents}'"))
def cache_file_contains(cache_context, contents):
    cache_context["file"].parent.mkdir(parents=True, exist_ok=True)
    cache_context["file"].write_text(contents)


@given(parsers.parse('writing the cache fails with "{message}"'))
def cache_write_fails(monkeypatch, message):
    def failing_replace(source, destination):
        raise OSError(message)

    monkeypatch.setattr("modules.cache.os.replace", failing_replace)


@when(parsers.parse('"{name}" is rewritten'))
def file_rewritten(cache_context, name):
    path = rom(cache_context, name)
    path.write_bytes(path.read_bytes() + b" and more")


@when(parsers.parse('"{name}" is moved to "{destination}"'))
def file_moved(cache_context, name, destination):
    source = rom(cache_context, name)
    target = rom(cache_context, destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)
    cache_context["cache"].moved(source, target)


@when(parsers.parse('"{name}" is deleted'))
def file_deleted(cache_context, name):
    rom(cache_context, name).unlink()


@when("the cache is saved and loaded again")
def cache_saved_and_loaded(cache_context):
    cache_context["cache"].save()
    cache_context["cache"] = FileCache(cache_context["file"])


@when("the cache is loaded")
def cache_loaded(cache_context):
    cache_context["cache"] = FileCache(cache_context["file"])


@when("the cache is saved")
def cache_saved(cache_context):
    try:
        cache_context["cache"].save()
    except OSError as e:
        cache_context["raised"] = e


@then(parsers.parse('the cache should know "{name}" has checksum "{md5}"'))
def cache_knows(cache_context, name, md5):
    assert cache_context["cache"].get(rom(cache_context, name))["md5"] == md5


@then(parsers.parse('the cache should know nothing about "{name}"'))
def cache_knows_nothing(cache_context, name):
    assert cache_context["cache"].get(rom(cache_context, name)) is None


@then(parsers.parse('the cache should hold only "{name}"'))
def cache_holds_only(cache_context, name):
    assert list(cache_context["cache"].entries) == [os.path.abspath(rom(cache_context, name))]


@then(parsers.parse('the library checksums should be "{checksums}"'))
def library_checksums(cache_context, checksums):
    assert sorted(cache_context["cache"].library_hashes()) == checksums.split(", ")


@then("the cache should be empty")
def cache_empty(cache_context):
    assert cache_context["cache"].entries == {}


@then(parsers.parse('saving the cache should raise "{message}"'))
def cache_save_raised(cache_context, message):
    assert message in str(cache_context["raised"])


@then("no temporary cache files should be left")
def no_temporary_cache_files(cache_context):
    assert not list(cache_context["file"].parent.glob(".files-*.json"))


@when("an unknown file is moved")
def unknown_file_moved(cache_context):
    cache_context["cache"].moved(rom(cache_context, "Unknown.sfc"), rom(cache_context, "snes/Unknown.sfc"))


@when(parsers.parse('everything under "{folder}" is forgotten'))
def forget_folder(cache_context, folder):
    cache_context["forgotten"] = cache_context["cache"].forget_under(rom(cache_context, folder))


@then(parsers.parse("{count:d} entry should have been forgotten"))
def entries_forgotten(cache_context, count):
    assert cache_context["forgotten"] == count
