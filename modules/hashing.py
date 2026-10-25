import hashlib
import zipfile

from modules.archives import zip_rom_member


def _hash_stream(f):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    while chunk := f.read(1024 * 1024):
        md5.update(chunk)
        sha1.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest()
    }


def hash_file(path):
    with open(path, "rb") as f:
        return _hash_stream(f)


def hash_rom(path):
    """
    Hash a ROM for DAT lookups. A zip holding a single ROM is hashed by its
    contents, since DATs list the ROM inside rather than the archive.
    """
    member = zip_rom_member(path)

    if member:
        with zipfile.ZipFile(path) as zf, zf.open(member) as f:
            return _hash_stream(f)

    return hash_file(path)
