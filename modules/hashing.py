import hashlib
import os
import zipfile

from modules.archives import zip_rom_member

CHUNK_SIZE = 8 * 1024 * 1024
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


def hash_file(path, progress=None):
    with open(path, "rb") as f:
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
