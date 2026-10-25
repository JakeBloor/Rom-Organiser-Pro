"""
Reading and writing .m3u playlists: one entry per line, relative to the playlist.
"""


def read_m3u(path):
    """The entries in a playlist, without blank lines or # comments."""
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except OSError:
        return []
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def write_m3u(path, entries):
    path.write_text("".join(entry + "\n" for entry in entries), encoding="utf-8")
