"""
Step implementations for looking inside ROM files
"""

import zipfile

import pytest
from pytest_bdd import given, scenario, scenarios, then, when, parsers

from modules.archives import (
    ISO_PVD_OFFSET,
    RAW_PVD_OFFSET,
    sheet_tracks,
    sniff_disc_system,
    zip_rom_member,
)


def volume_descriptor(offset, system_id, boot_line=b""):
    """An ISO 9660 primary volume descriptor at offset, then SYSTEM.CNF text."""
    image = bytearray(offset + 0x800)
    image[offset : offset + 6] = b"\x01CD001"
    image[offset + 8 : offset + 40] = system_id.ljust(32)
    return bytes(image) + boot_line


def with_bytes_at(offset, value):
    image = bytearray(0x200)
    image[offset : offset + len(value)] = value
    return bytes(image)


DISC_HEADERS = {
    "GameCube": with_bytes_at(0x1C, bytes.fromhex("C2339F3D")),
    "Wii": with_bytes_at(0x18, bytes.fromhex("5D1C9EA3")),
    "Saturn": with_bytes_at(0x10, b"SEGA SEGASATURN "),
    "Sega CD": with_bytes_at(0x10, b"SEGADISCSYSTEM  "),
    "Dreamcast": with_bytes_at(0x00, b"SEGA SEGAKATANA "),
    "Genesis": with_bytes_at(0x100, b"SEGA MEGA DRIVE "),
    "PSP": volume_descriptor(ISO_PVD_OFFSET, b"PSP GAME"),
    "PS1": volume_descriptor(ISO_PVD_OFFSET, b"PLAYSTATION", b"BOOT = cdrom:\\SCUS_942.36;1\r\n"),
    "PS2": volume_descriptor(ISO_PVD_OFFSET, b"PLAYSTATION", b"BOOT2 = cdrom0:\\SLUS_206.92;1\r\n"),
    "raw PS1": volume_descriptor(RAW_PVD_OFFSET, b"PLAYSTATION", b"BOOT=cdrom:\\SLUS_000.67;1\r\n"),
    "PlayStation, no boot": volume_descriptor(ISO_PVD_OFFSET, b"PLAYSTATION"),
    "unknown": b"just some bytes" * 100,
}


@pytest.fixture
def archive_context(tmp_path):
    return {"tmp": tmp_path}


scenarios("../features/archives.feature")


@given(parsers.parse("a disc image with a {header} header"))
def disc_image_with_header(archive_context, header):
    image = archive_context["tmp"] / "disc.iso"
    image.write_bytes(DISC_HEADERS[header])
    archive_context["image"] = image


@when("the disc image is sniffed")
def disc_image_sniffed(archive_context):
    archive_context["sniffed"] = sniff_disc_system(archive_context["image"])


@when("a missing disc image is sniffed")
def missing_disc_image_sniffed(archive_context):
    archive_context["sniffed"] = sniff_disc_system(archive_context["tmp"] / "missing.iso")


@then(parsers.parse('the sniffed system should be "{system}"'))
def sniffed_system_is(archive_context, system):
    assert archive_context["sniffed"] == (None if system == "none" else system)


@given(parsers.parse('a zip holding "{first}" and "{second}"'))
def zip_holding(archive_context, first, second):
    path = archive_context["tmp"] / "game.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("roms/", b"")  # directory entries don't count as ROMs
        zf.writestr(first, b"one")
        zf.writestr(second, b"two")
    archive_context["zip"] = path


@given("a damaged zip")
def damaged_zip(archive_context):
    path = archive_context["tmp"] / "damaged.zip"
    path.write_bytes(b"PK\x03\x04 not really a zip")
    archive_context["zip"] = path


@then("the zip should have no single ROM")
def zip_has_no_single_rom(archive_context):
    assert zip_rom_member(archive_context["zip"]) is None


@then(parsers.parse("the zip's single ROM should be \"{member}\""))
def zip_single_rom_is(archive_context, member):
    assert zip_rom_member(archive_context["zip"]) == member


@given(
    parsers.parse(
        'a cue sheet pointing at "{first}", "{second}" and "{repeat}" where track 2 is missing'
    )
)
def cue_sheet_with_missing_track(archive_context, first, second, repeat):
    tmp = archive_context["tmp"]
    (tmp / first).write_bytes(b"track 1")
    sheet = tmp / "Game.cue"
    sheet.write_text(
        f'FILE "{first}" BINARY\n  TRACK 01 MODE2/2352\n'
        f'FILE "{second}" BINARY\n  TRACK 02 AUDIO\n'
        f"FILE {repeat.replace(' ', '_')} BINARY\n"
        f'file "{repeat}" binary\n'
    )
    archive_context["sheet"] = sheet


@given(parsers.parse('a gdi sheet pointing at "{first}" and "{second}"'))
def gdi_sheet(archive_context, first, second):
    tmp = archive_context["tmp"]
    (tmp / first).write_bytes(b"track 1")
    (tmp / second).write_bytes(b"track 2")
    sheet = tmp / "Game.gdi"
    sheet.write_text(f'2\n1 0 4 2352 {first} 0\n2 600 0 2352 "{second}" 0\n')
    archive_context["sheet"] = sheet


@then(parsers.parse('the sheet\'s tracks should be "{names}"'))
def sheet_tracks_are(archive_context, names):
    tracks = sheet_tracks(archive_context["sheet"])
    assert [track.name for track in tracks] == names.split(", ")


@then("a missing sheet should have no tracks")
def missing_sheet_has_no_tracks(archive_context):
    assert sheet_tracks(archive_context["tmp"] / "missing.cue") == []
