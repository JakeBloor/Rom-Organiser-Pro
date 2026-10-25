import hashlib
import os
import zipfile

from modules.archives import zip_rom_member

CHUNK_SIZE = 8 * 1024 * 1024
# SNES dumps from copier devices start with a 512-byte header DATs don't include
SNES_SUFFIXES = (".smc", ".sfc", ".fig", ".swc")
SNES_COPIER_HEADER = 512
# Where each CHD header version keeps its SHA-1s: of the raw data (for a
# DVD-based game, the original image), and overall
CHD_MAGIC = b"MComprHD"
CHD_SHA1_OFFSETS = {3: (0x50,), 4: (0x58, 0x30), 5: (0x40, 0x54)}
# Bytes read from the start, middle and end of a file for its fingerprint
FINGERPRINT_SAMPLE = 1024 * 1024


def _hash_stream(f, progress=None):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    while chunk := f.read(CHUNK_SIZE):
        md5.update(chunk)
        sha1.update(chunk)
        if progress:
            progress(len(chunk))

    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest()
    }


def _header_size(name, size):
    if name.lower().endswith(SNES_SUFFIXES) and size % 1024 == SNES_COPIER_HEADER:
        return SNES_COPIER_HEADER
    return 0


def hash_file(path, progress=None):
    with open(path, "rb") as f:
        f.seek(_header_size(str(path), os.path.getsize(path)))
        return _hash_stream(f, progress)


def hash_rom(path, progress=None):
    """
    Hash a ROM for DAT lookups. A zip holding a single ROM is hashed by its
    contents, since DATs list the ROM inside rather than the archive.
    progress, if given, is called with the size of each chunk as it is read.
    """
    member = zip_rom_member(path)

    if member:
        with zipfile.ZipFile(path) as zf, zf.open(member) as f:
            f.read(_header_size(member, zf.getinfo(member).file_size))
            return _hash_stream(f, progress)

    return hash_file(path, progress)


def fingerprint(path):
    """
    A quick identity for a large file: its size and samples from its start,
    middle and end. Enough to spot the same file dropped in twice without
    reading gigabytes; not usable for DAT lookups.
    """
    size = os.path.getsize(path)
    digest = hashlib.md5(str(size).encode())

    with open(path, "rb") as f:
        for offset in sorted({0, max(0, size // 2 - FINGERPRINT_SAMPLE // 2), max(0, size - FINGERPRINT_SAMPLE)}):
            f.seek(offset)
            digest.update(f.read(FINGERPRINT_SAMPLE))

    return "fp:" + digest.hexdigest()


def chd_sha1s(path):
    """
    The SHA-1s a CHD's header records, without reading the rest of it. For a
    DVD-based game (PS2, PSP) the raw-data SHA-1 is that of the original
    image, so it matches the Redump DAT. Empty if it isn't a CHD.
    """
    with open(path, "rb") as f:
        header = f.read(0x7C)

    if header[:8] != CHD_MAGIC or len(header) < 16:
        return []

    version = int.from_bytes(header[12:16], "big")
    found = []
    for offset in CHD_SHA1_OFFSETS.get(version, ()):
        digest = header[offset:offset + 20]
        if len(digest) == 20 and any(digest):
            found.append(digest.hex())
    return found
