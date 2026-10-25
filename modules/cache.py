"""
What the app has learned about files in the ROM folder, so it doesn't have to
work it out again. Each entry is keyed by the file's path and only trusted
while the file's size and modification time are unchanged:

- checksums (or, for big and compressed images, a quick fingerprint), so
  files aren't read again on every run, and a game dropped in a second time
  is recognised as one already in the library
- the outcome of the last run for files left where they were (unsorted,
  skipped or a duplicate), so new files can be told apart from ones that
  need you to do something

Kept in cache/files.json in the app folder. Deleting it is always safe: the
app just hashes and checks files again.
"""

import json
import os
import tempfile
import threading
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parent.parent / "cache" / "files.json"
# 2: entries carry an "identity" (checksum or fingerprint)
CACHE_VERSION = 2

# Outcomes of files a run left where they were
LEFT_IN_PLACE = ("unsorted", "skipped", "duplicate")


def _key(path):
    return os.path.abspath(path)


def _stamp(path):
    stat = os.stat(path)
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


class FileCache:
    def __init__(self, path=None):
        self.path = Path(path or CACHE_FILE)
        self.entries = {}
        # The organise worker and page requests share one cache
        self.lock = threading.RLock()
        self.load()

    def load(self):
        try:
            stored = json.loads(self.path.read_text())
        except (OSError, ValueError):
            stored = {}

        with self.lock:
            files = stored.get("files") if isinstance(stored, dict) else None
            current = isinstance(files, dict) and stored.get("version") == CACHE_VERSION
            self.entries = files if current else {}

    def get(self, path):
        """The entry for path, or None if there isn't one or the file has changed."""
        with self.lock:
            entry = self.entries.get(_key(path))
            if entry is None:
                return None
            try:
                stamp = _stamp(path)
            except OSError:
                return None
            matches = all(entry.get(field) == value for field, value in stamp.items())
            return entry if matches else None

    def remember(self, path, **fields):
        """Records fields for path, keeping what's known unless the file has changed."""
        with self.lock:
            self.entries[_key(path)] = {**(self.get(path) or {}), **fields, **_stamp(path)}

    def moved(self, source, destination):
        """Moves source's entry to destination; a move keeps size and modification time."""
        with self.lock:
            entry = self.entries.pop(_key(source), None)
            if entry is not None:
                self.entries[_key(destination)] = entry

    def library_hashes(self):
        """{identity: path} for the games the app has organised that are still where it put them."""
        with self.lock:
            return {
                entry["identity"]: Path(key)
                for key, entry in list(self.entries.items())
                if entry.get("outcome") == "organised" and "identity" in entry and self.get(key)
            }

    def save(self):
        """Writes the cache, dropping entries for files that have gone or changed."""
        with self.lock:
            self.entries = {key: entry for key, entry in self.entries.items() if self.get(key)}
            data = {"version": CACHE_VERSION, "files": self.entries}

            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=".files-", suffix=".json")
            try:
                with os.fdopen(fd, "w") as file:
                    json.dump(data, file)
                os.replace(temporary, self.path)
            except BaseException:
                os.unlink(temporary)
                raise
