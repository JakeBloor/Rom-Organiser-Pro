"""
Step implementations for looking inside ROM files
"""

import re
import struct
import zipfile
from pathlib import Path

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


@given("two copies of a 3 MB file and a third that differs only in the middle")
def fingerprint_files(tmp_path, archive_context):
    from modules.hashing import FINGERPRINT_SAMPLE

    data = bytearray(3 * FINGERPRINT_SAMPLE)
    for name in ("a.iso", "b.iso"):
        (tmp_path / name).write_bytes(data)
    data[len(data) // 2] = 1
    (tmp_path / "c.iso").write_bytes(data)
    archive_context["dir"] = tmp_path


@then("the copies should have the same fingerprint")
def same_fingerprint(archive_context):
    from modules.hashing import fingerprint

    folder = archive_context["dir"]
    assert fingerprint(folder / "a.iso") == fingerprint(folder / "b.iso")


@then("the third should have a different fingerprint")
def different_fingerprint(archive_context):
    from modules.hashing import fingerprint

    folder = archive_context["dir"]
    assert fingerprint(folder / "c.iso") != fingerprint(folder / "a.iso")


@then("hashing a ROM without watching progress should still give its MD5")
def hash_without_progress(archive_context):
    import hashlib

    from modules.hashing import hash_rom

    path = archive_context["dir"] / "a.iso"
    assert hash_rom(path)["md5"] == hashlib.md5(path.read_bytes()).hexdigest()


@given(parsers.re(r"a PS3 game folder whose (?P<where>disc|installed) PARAM\.SFO is (?P<contents>.+)"))
def ps3_folder_with_sfo(tmp_path, archive_context, where, contents):
    from tests.sfo import make_sfo

    folder = tmp_path / "BLUS30001"
    sfo = folder / ("PS3_GAME/PARAM.SFO" if where == "disc" else "PARAM.SFO")
    sfo.parent.mkdir(parents=True)
    titled = re.fullmatch(r'titled "(.*)"', contents)
    if titled:
        sfo.write_bytes(make_sfo({"TITLE_ID": "NPUA80068", "TITLE": titled.group(1)}))
    elif contents == "not a PARAM.SFO":
        sfo.write_bytes(b"NOPE" + bytes(40))
    elif contents == "cut short":
        sfo.write_bytes(make_sfo({"TITLE": "Demon's Souls"})[:24])
    elif contents == "without a title":
        sfo.write_bytes(make_sfo({"TITLE_ID": "BLUS30001"}))
    archive_context["ps3_folder"] = folder


@then(parsers.re(r'its title should be "(?P<title>.*)"'))
def ps3_folder_title(archive_context, title):
    from modules.archives import ps3_title

    assert ps3_title(archive_context["ps3_folder"]) == (title or None)


CHD_OFFSETS = {5: (0x40, 0x54), 4: (0x58, 0x30), 3: (0x50, 0x64)}


@given(parsers.parse('a version {version:d} CHD header recording SHA-1s "{raw}" and "{overall}"'))
def chd_header(tmp_path, archive_context, version, raw, overall):
    header = bytearray(0x7C)
    header[:8] = b"MComprHD"
    header[12:16] = version.to_bytes(4, "big")
    for offset, digest in zip(CHD_OFFSETS.get(version, CHD_OFFSETS[5]), (raw, overall)):
        header[offset:offset + 20] = bytes.fromhex(digest)
    path = tmp_path / "game.chd"
    path.write_bytes(bytes(header) + b"compressed hunks")
    archive_context["chd"] = path


@given(parsers.parse('a file "{name}" that isn\'t a CHD'))
def not_a_chd(tmp_path, archive_context, name):
    archive_context["chd"] = tmp_path / name
    archive_context["chd"].write_bytes(b"short")


@then(parsers.re(r'the CHD SHA-1s should be "(?P<found>[^"]*)"'))
def chd_sha1s_are(archive_context, found):
    from modules.hashing import chd_sha1s

    assert chd_sha1s(archive_context["chd"]) == [h for h in found.split(", ") if h]


def _nintendo_header(serial, wii):
    header = bytearray(0x20)
    header[:6] = serial.encode()
    if wii:
        header[0x18:0x1C] = bytes.fromhex("5D1C9EA3")
    else:
        header[0x1C:0x20] = bytes.fromhex("C2339F3D")
    return bytes(header)


@given(parsers.parse('a {kind} disc image "{name}" with serial "{serial}"'))
def disc_image_with_serial(tmp_path, archive_context, kind, name, serial):
    from modules.archives import NINTENDO_ID_OFFSETS
    from tests.sfo import make_sfo

    path = tmp_path / name
    suffix = path.suffix.lower()
    if kind in ("GameCube", "Wii"):
        offset = NINTENDO_ID_OFFSETS[suffix]
        path.write_bytes(bytes(offset) + _nintendo_header(serial, kind == "Wii") + bytes(64))
    elif kind == "PBP":
        sfo = make_sfo({"DISC_ID": serial, "TITLE": "Crash"})
        header = b"\0PBP" + bytes(4) + struct.pack("<II", 0x28, 0x28 + len(sfo)) + bytes(0x28 - 16)
        path.write_bytes(header + sfo + b"icon")
    elif kind == "PSP":
        path.write_bytes(bytes(0x8000) + f"{serial[:4]}-{serial[4:]}|0001|G".encode())
    else:
        boot = "BOOT2" if kind == "PlayStation 2" else "BOOT"
        system_cnf = f"{boot} = cdrom0:\\{serial[:4]}_{serial[4:7]}.{serial[7:]};1\r\n"
        path.write_bytes(bytes(0x9000) + system_cnf.encode())
    archive_context["serial_file"] = path


@given(parsers.re(r'a file "(?P<name>[^"]+)" containing "(?P<contents>[^"]*)"'))
def file_containing(tmp_path, archive_context, name, contents):
    path = tmp_path / name
    if contents:
        path.write_bytes(contents.encode())
    archive_context["serial_file"] = path


@then(parsers.re(r'its serial should be "(?P<serial>[^"]*)"'))
def serial_is(archive_context, serial):
    from modules.archives import disc_serial

    assert disc_serial(archive_context["serial_file"]) == (serial or None)


@then(parsers.re(r'its PS3 serial should be "(?P<serial>[^"]*)"'))
def ps3_serial_is(archive_context, serial):
    from modules.archives import ps3_serial

    assert ps3_serial(archive_context["ps3_folder"]) == (serial or None)


@given(parsers.parse('a cue sheet "{name}" pointing at "{track}"'))
def cue_pointing_at(tmp_path, archive_context, name, track):
    sheet = tmp_path / name
    sheet.write_text(f'FILE "{track}" BINARY\n')
    archive_context["sheet"] = sheet


@then("the sheet should have no tracks")
def sheet_has_no_tracks(archive_context):
    from modules.archives import sheet_tracks

    assert sheet_tracks(archive_context["sheet"]) == []


@given(parsers.parse('a Dreamcast sheet "{name}" with tracks "{first}", "{second}" and "{third}"'))
def gdi_sheet(tmp_path, archive_context, name, first, second, third):
    sheet = tmp_path / "dreamcast" / name
    sheet.parent.mkdir()
    sheet.write_text(f"3\n1 0 4 2352 {first} 0\n2 600 0 2352 {second} 0\n3 45000 4 2352 {third} 0\n")
    archive_context["sheet"] = sheet


@when(parsers.parse('the sheet\'s "{first}" moves to "{first_new}" and "{second}" to "{second_new}"'))
def sheet_tracks_move(archive_context, first, first_new, second, second_new):
    from modules.archives import rewrite_sheet

    folder = archive_context["sheet"].parent
    rewrite_sheet(archive_context["sheet"], {first: folder / first_new, second: folder / second_new})


@then(parsers.parse('the sheet should read "{lines}"'))
def sheet_reads(archive_context, lines):
    assert archive_context["sheet"].read_text().splitlines()[1:] == lines.split(" | ")
