"""
Unpacking .rar, .7z and .zip archives, including ones split into parts
("Game.part1.rar", "Game.7z.001"), with libarchive: the library behind
bsdtar, built into macOS and SteamOS. Its bsdtar command only opens one
file, but the library can read a set of parts as one archive.
"""

import ctypes
import ctypes.util
from pathlib import Path, PurePosixPath

ARCHIVE_OK = 0
ARCHIVE_EOF = 1
ARCHIVE_WARN = -20
REGULAR_FILE = 0o100000
BLOCK_SIZE = 1024 * 1024


class UnpackError(Exception):
    pass


_library = None


def _libarchive():
    global _library
    if _library is None:
        found = ctypes.util.find_library("archive")
        if not found:
            raise UnpackError("libarchive isn't installed, so archives can't be unpacked")
        lib = ctypes.CDLL(found)
        lib.archive_read_new.restype = ctypes.c_void_p
        for name in ("archive_read_support_format_all", "archive_read_support_filter_all",
                     "archive_read_free", "archive_read_data_skip"):
            getattr(lib, name).argtypes = [ctypes.c_void_p]
        lib.archive_read_open_filenames.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]
        lib.archive_read_next_header.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        lib.archive_read_data.restype = ctypes.c_ssize_t
        lib.archive_read_data.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        lib.archive_error_string.restype = ctypes.c_char_p
        lib.archive_error_string.argtypes = [ctypes.c_void_p]
        lib.archive_entry_pathname_utf8.restype = ctypes.c_char_p
        lib.archive_entry_pathname_utf8.argtypes = [ctypes.c_void_p]
        lib.archive_entry_filetype.restype = ctypes.c_uint
        lib.archive_entry_filetype.argtypes = [ctypes.c_void_p]
        _library = lib
    return _library


def _safe_name(name):
    """The entry's path, or None if it would write outside the target folder."""
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return None
    return path


def unpack(parts, destination, keep=None, on_file=None):
    """
    Unpacks an archive given as its parts, in order, into destination. Only
    regular files are written; keep, if given, picks which by path. Entries
    that would land outside destination are skipped. on_file is called with
    each written path. Returns how many files were written.
    """
    lib = _libarchive()
    destination = Path(destination)
    archive = lib.archive_read_new()
    try:
        lib.archive_read_support_format_all(archive)
        lib.archive_read_support_filter_all(archive)
        names = (ctypes.c_char_p * (len(parts) + 1))(*[str(p).encode() for p in parts], None)
        if lib.archive_read_open_filenames(archive, names, BLOCK_SIZE) != ARCHIVE_OK:
            raise UnpackError(_error(lib, archive))

        entry = ctypes.c_void_p()
        buffer = ctypes.create_string_buffer(BLOCK_SIZE)
        written = 0
        while True:
            result = lib.archive_read_next_header(archive, ctypes.byref(entry))
            if result == ARCHIVE_EOF:
                return written
            if result < ARCHIVE_WARN:
                raise UnpackError(_error(lib, archive))

            name = _safe_name(lib.archive_entry_pathname_utf8(entry).decode("utf-8", "replace"))
            wanted = name and lib.archive_entry_filetype(entry) == REGULAR_FILE and (keep is None or keep(name))
            if not wanted:
                lib.archive_read_data_skip(archive)
                continue

            target = destination.joinpath(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as file:
                while (count := lib.archive_read_data(archive, buffer, BLOCK_SIZE)) > 0:
                    file.write(buffer.raw[:count])
            if count < 0:
                target.unlink()
                raise UnpackError(f"{name}: {_error(lib, archive)}")
            written += 1
            if on_file:
                on_file(target)
    finally:
        lib.archive_read_free(archive)


def _error(lib, archive):
    message = lib.archive_error_string(archive)
    return message.decode("utf-8", "replace") if message else "unreadable archive"
