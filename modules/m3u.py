from pathlib import Path

def parse_m3u(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def append_to_m3u(folder, game_name, filename):
    m3u = folder / f"{game_name}.m3u"

    entries = []

    if m3u.exists():
        entries = m3u.read_text().splitlines()

    if filename not in entries:
        with open(m3u, "a", encoding="utf-8") as f:
            f.write(filename + "\n")