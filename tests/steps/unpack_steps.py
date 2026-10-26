"""
Step implementations for unpacking archives with libarchive
"""

import io
import os
import zipfile

import pytest
from pytest_bdd import given, scenarios, then, when, parsers

from modules import unpack


@pytest.fixture
def unpack_context(tmp_path):
    return {"tmp": tmp_path, "parts": [], "destination": tmp_path / "out" / "unpacked"}


scenarios("../features/unpack.feature")


def write_zip(entries):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return data.getvalue()


def split(unpack_context, data, count):
    size = len(data) // count + 1
    for index in range(count):
        part = unpack_context["tmp"] / f"pack.zip.{index + 1:03}"
        part.write_bytes(data[index * size:(index + 1) * size])
        unpack_context["parts"].append(part)


@given(parsers.parse("an archive of {count:d} images split into {parts:d} parts"))
def split_archive(unpack_context, count, parts):
    # Random bytes don't compress, so every part holds some of each image
    images = {f"Game {index} (USA).png": os.urandom(20000) for index in range(count)}
    unpack_context["images"] = images
    split(unpack_context, write_zip(images), parts)


@given(parsers.parse('an archive holding "{first}", "{second}" and the folder "{folder}"'))
def archive_with_folder(unpack_context, first, second, folder):
    split(unpack_context, write_zip({first: b"image", second: b"text", folder: b""}), 1)


@given(parsers.parse('an archive holding "{first}", "{second}" and "{third}"'))
def archive_with_unsafe(unpack_context, first, second, third):
    split(unpack_context, write_zip({first: b"bad", second: b"bad", third: b"good"}), 1)


@given("a file that isn't an archive")
def not_an_archive(unpack_context):
    split(unpack_context, b"this is not an archive at all" * 10, 1)


@given("the archive's last part is missing")
def last_part_missing(unpack_context):
    unpack_context["parts"].pop().unlink()


@given("libarchive isn't installed")
def no_libarchive(unpack_context, monkeypatch):
    monkeypatch.setattr(unpack, "_library", None)
    monkeypatch.setattr(unpack.ctypes.util, "find_library", lambda name: None)
    split(unpack_context, write_zip({"a.png": b"a"}), 1)


@when("the archive is unpacked")
def archive_unpacked(unpack_context):
    unpack_context["count"] = unpack.unpack(unpack_context["parts"], unpack_context["destination"])


@when("the archive is unpacked keeping only images")
def archive_unpacked_images(unpack_context):
    written = unpack_context["written"] = []
    unpack_context["count"] = unpack.unpack(
        unpack_context["parts"], unpack_context["destination"],
        keep=lambda path: path.suffix == ".png", on_file=written.append,
    )


@when("unpacking it is tried")
def unpacking_tried(unpack_context):
    try:
        unpack.unpack(unpack_context["parts"], unpack_context["destination"])
    except unpack.UnpackError as e:
        unpack_context["error"] = e


@then(parsers.parse("{count:d} images should have been unpacked"))
def images_unpacked(unpack_context, count):
    assert unpack_context["count"] == count


@then("the unpacked images should match the originals")
def images_match(unpack_context):
    for name, content in unpack_context["images"].items():
        assert (unpack_context["destination"] / name).read_bytes() == content


@then(parsers.parse('the unpacked files should be "{names}"'))
def unpacked_files(unpack_context, names):
    destination = unpack_context["destination"]
    found = sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file())
    assert found == names.split(", ")


@then("nothing should have been written outside the target folder")
def nothing_outside(unpack_context):
    outside = [p for p in unpack_context["tmp"].rglob("*.png") if unpack_context["destination"] not in p.parents]
    assert outside == []


@then("unpacking should fail")
def unpacking_failed(unpack_context):
    assert isinstance(unpack_context["error"], unpack.UnpackError)


@then(parsers.parse('unpacking should fail with "{message}"'))
def unpacking_failed_with(unpack_context, message):
    assert message in str(unpack_context["error"])


@then("no unpacked file should be left half written")
def no_half_files(unpack_context):
    destination = unpack_context["destination"]
    for path in destination.rglob("*.png") if destination.exists() else ():
        assert path.read_bytes() in unpack_context["images"].values()


@given("an archive whose second entry is damaged")
def damaged_second_entry(unpack_context):
    data = bytearray(write_zip({"first.png": b"first image", "second.png": b"second image"}))
    second = data.index(b"PK\x03\x04", 4)
    data[second:second + 4] = b"JUNK"
    split(unpack_context, bytes(data), 1)
