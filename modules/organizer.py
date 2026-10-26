import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

from config import (
    AMBIGUOUS_EXTENSIONS,
    DAT_SYSTEM_IDS,
    M3U_SYSTEMS,
    MULTI_FILE_DIR,
    SYSTEM_MAP,
    SYSTEM_ROM_TYPES,
    canonical_system,
)
from modules import esde, settings
from modules.archives import (
    disc_serial,
    is_ps3_folder,
    ps3_serial,
    ps3_title,
    rewrite_sheet,
    sheet_tracks,
)
import time

from modules.hashing import chd_sha1s, fingerprint, hash_rom
from modules.dat_validation import lookup_hashes, lookup_name, lookup_serial
from modules.detection import DISC_REGEX, _accepts, detect_system, clean_name, get_disc_number
from modules.m3u import read_m3u, write_m3u

ARCADE_SYSTEMS = {"fbneo", "arcade", "mame"}
SHEET_SUFFIXES = {".cue", ".gdi"}
SYSTEM_FOLDERS = set(SYSTEM_ROM_TYPES) | set(DAT_SYSTEM_IDS.values())
# Compressed disc and archive formats: DATs list the uncompressed images, so
# these never match one and are only fingerprinted
UNMATCHABLE_SUFFIXES = {
    ".chd", ".rvz", ".gcz", ".wia", ".wbfs", ".cso", ".zso", ".isz", ".pbp",
    ".ecm", ".7z", ".rar", ".nsz", ".wux", ".wua",
}


def _bump(status, key, amount=1):
    status[key] = status.get(key, 0) + amount


def _playlist_title(name):
    """"Final Fantasy VII (USA) (Disc 1)" -> "Final Fantasy VII (USA)"."""
    title = DISC_REGEX.sub("", name)
    title = re.sub(r"\(\s*\)|\[\s*\]", "", title)
    return re.sub(r"\s+", " ", title).strip(" -_")


def is_rom_candidate(path):
    suffix = path.suffix.lower()
    return suffix in SYSTEM_MAP or suffix in AMBIGUOUS_EXTENSIONS


def _uses_shared_layout(system):
    """Whether a multi-file game for system gets a playlist pointing into MULTI_FILE_DIR."""
    return settings.get("multi_file_layout") == "shared" and system in M3U_SYSTEMS


def stores_multi_file_games_apart(system):
    """
    Whether a multi-file game (a .cue/.gdi with tracks, or one disc of several)
    sitting in system's folder still needs organising: moving behind a playlist,
    or into a folder ES-DE launches as one game.
    """
    return system not in ARCADE_SYSTEMS and (
        _uses_shared_layout(system) or settings.get("multi_file_layout") == "esde"
    )


def _identify(path, cache, on_bytes=None):
    """
    Checksums for a DAT lookup, or just a fingerprint for files that can't
    match a DAT (compressed images) or are too big to be worth reading in
    full. A CHD also gives the SHA-1s in its header. Either way "identity"
    tells duplicates apart. Reuses the cache.
    """
    entry = cache.get(path) if cache else None
    if entry and "identity" in entry:
        return {key: entry[key] for key in HASH_FIELDS if key in entry}

    limit = settings.get("dat_check_limit_mb") * 1024 * 1024
    if path.suffix.lower() == ".chd":
        hashes = {"identity": fingerprint(path)}
        for key, sha1 in zip(("sha1", "sha1_overall"), chd_sha1s(path)):
            hashes[key] = sha1
    elif path.suffix.lower() in UNMATCHABLE_SUFFIXES or path.stat().st_size > limit:
        hashes = {"identity": fingerprint(path)}
    else:
        hashes = hash_rom(path, on_bytes)
        hashes["identity"] = hashes["md5"]

    serial = disc_serial(path)
    if serial:
        hashes["serial"] = serial

    if cache:
        cache.remember(path, **hashes)
    return hashes


HASH_FIELDS = ("md5", "sha1", "sha1_overall", "serial", "identity")


def _dat_hashes(hashes):
    return {key: value for key, value in hashes.items() if key not in ("identity", "serial")}


def _miss_reason(path, hashes):
    """Why a game matched no DAT entry, for the run report."""
    if path.suffix.lower() in UNMATCHABLE_SUFFIXES:
        return "compressed image, and its serial and name aren't in the DATs"
    if "md5" not in hashes:
        return "too big to check, and its serial and name aren't in the DATs"
    return "not in the DATs: renamed, patched, a hack or homebrew"


def game_logger(logger, system, game, *roots):
    """
    A logger naming the system and game in each line, e.g. "[MOVED] psx ·
    Final Fantasy VII (USA) · ...", with paths shown relative to roots.
    """
    prefixes = sorted((f"{root}/" for root in roots if root), key=len, reverse=True)
    label = f"{system or 'unknown system'} · {game}"

    def log(message, level="INFO"):
        for prefix in prefixes:
            message = message.replace(prefix, "")
        tag, separator, rest = message.partition("] ")
        logger(f"{tag}] {label} · {rest}" if separator else f"{label} · {message}", level)

    return log


def _identified(log, matched_by, dat_title, hashes, reason):
    """Logs how a game was identified, and from which DAT."""
    if matched_by == "serial":
        log(f"[IDENTIFIED] matched by serial {hashes['serial']} in {dat_title}")
    elif matched_by:
        log(f"[IDENTIFIED] matched by {matched_by} in {dat_title}")
    else:
        log(f"[IDENTIFIED] no DAT match: {reason}")


def _priority_key(path, rom_root):
    """Sorts files so the priority systems' come first, in their order."""
    priority = settings.priority_systems()
    system = _system_folder(path, rom_root) or SYSTEM_MAP.get(path.suffix.lower())
    rank = priority.index(system) if system in priority else len(priority)
    return rank, str(path)


def sort_by_priority(systems):
    """System names with the priority ones first, in their order, then the rest alphabetically."""
    priority = settings.priority_systems()
    return sorted(systems, key=lambda s: (priority.index(s) if s in priority else len(priority), s))


def _remember(cache, path, **fields):
    if cache:
        cache.remember(path, **fields)


def _remove_emptied_folders(folders, top):
    """
    Removes folders a run emptied, and their emptied parents, up to (not
    including) top. System folders directly under top are always kept.
    """
    for folder in sorted(folders, key=lambda f: len(f.parts), reverse=True):
        while top in folder.parents and not (folder.parent == top and folder.name in SYSTEM_FOLDERS):
            try:
                folder.rmdir()
            except OSError:
                break
            folder = folder.parent


def repair_playlists(rom_root, logger, dry_run=False):
    """
    Drops dead entries from the playlists the app made (ones listing files in
    MULTI_FILE_DIR), such as entries left behind when discs moved. Playlists
    you wrote yourself are left alone. Returns how many were repaired.
    """
    rom_root = Path(rom_root)
    repaired = 0

    for playlist in sorted(rom_root.glob("*/*.m3u")):
        if not playlist.is_file() or playlist.parent.name.startswith("."):
            continue
        entries = read_m3u(playlist)
        if not any(MULTI_FILE_DIR in Path(entry).parts for entry in entries):
            continue
        working = [entry for entry in entries if (playlist.parent / entry).is_file()]
        if working == entries or not working:
            continue

        repaired += 1
        dead = len(entries) - len(working)
        if dry_run:
            log = game_logger(logger, playlist.parent.name, playlist.stem, rom_root)
            log(f"[DRY RUN] would drop {dead} entries that lead nowhere")
        else:
            write_m3u(playlist, working)
            log = game_logger(logger, playlist.parent.name, playlist.stem, rom_root)
            log(f"[PLAYLIST] dropped {dead} entries that led nowhere")

    return repaired


def _write_playlist(playlist_dir, title, entries, logger, dry_run):
    """
    Writes the game's playlist. Entries of an existing one that still lead to
    a file (say, discs organised on an earlier run) are kept; ones that
    don't, like discs that have just moved, are dropped. Discs go in order.
    """
    playlist = playlist_dir / f"{title}.m3u"
    new_targets = {os.path.normpath(playlist_dir / entry) for entry in entries}
    kept = [
        entry
        for entry in read_m3u(playlist)
        if (playlist_dir / entry).is_file() and os.path.normpath(playlist_dir / entry) not in new_targets
    ]
    combined = sorted(kept + entries, key=lambda entry: get_disc_number(Path(entry).stem) or 0)

    if dry_run:
        logger(f"[DRY RUN] {playlist} lists: {', '.join(combined)}")
        return

    # In the shared layout the system folder may not exist yet
    playlist_dir.mkdir(parents=True, exist_ok=True)
    write_m3u(playlist, combined)


def _replaceable_playlist(playlist, unit):
    """
    Whether an existing playlist can be rewritten for this game: every entry
    names one of the game's own files (a playlist you made for it). A
    playlist listing anything else is never touched.
    """
    names = {f.name.lower() for f in unit}
    return all(Path(entry).name.lower() in names for entry in read_m3u(playlist))


def _place(unit, dest_dir, logger, status, dry_run, planned, playlist=None, cache=None):
    """
    Move a ROM and the files that belong with it into dest_dir, never
    overwriting. playlist is the game's .m3u; it may already exist only if it
    lists nothing but this game (see _replaceable_playlist).
    """
    destinations = [dest_dir / f.name for f in unit]

    # Dropped straight into the right folder: organised where it is
    if destinations == list(unit):
        logger(f"[IN PLACE] {unit[0]}")
        planned.update(destinations)
        _bump(status, "roms_processed")
        return True

    clash = next((d for d in destinations if d.exists() or d in planned), None)
    if clash is None and playlist and (
        playlist in planned or (playlist.exists() and not _replaceable_playlist(playlist, unit))
    ):
        clash = playlist
    if clash is None and dest_dir.exists() and not dest_dir.is_dir():
        clash = dest_dir

    if clash is not None:
        logger(f"[SKIP] {clash} already exists, leaving {unit[0]} in place")
        _bump(status, "skipped")
        _remember(cache, unit[0], outcome="skipped")
        return False

    planned.update(destinations)
    if playlist:
        planned.add(playlist)

    for source, destination in zip(unit, destinations):
        if dry_run:
            logger(f"[DRY RUN] {source} -> {destination}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            if cache:
                cache.moved(source, destination)
            logger(f"[MOVED] {source} -> {destination}")

    _bump(status, "roms_processed")
    return True


def _place_sheet_hiding_tracks(sheet, tracks, rom_root, system, logger, status, dry_run, planned, cache, emptied):
    """
    For systems whose Steam parser can't launch a playlist: the .cue or .gdi
    stays in the system folder and its tracks move into MULTI_FILE_DIR, with
    the sheet pointed at them, so ES-DE and Steam each list one file.
    """
    sheet_dest = rom_root / system / sheet.name
    track_dir = rom_root / MULTI_FILE_DIR / system / sheet.stem
    moves = [(track, track_dir / track.name) for track in tracks if track.parent != track_dir]
    if sheet != sheet_dest:
        moves.append((sheet, sheet_dest))

    if not moves:
        logger(f"[IN PLACE] {sheet}")
        _bump(status, "roms_processed")
        return True

    clash = next((dest for _, dest in moves if dest.exists() or dest in planned), None)
    if clash is not None:
        logger(f"[SKIP] {clash} already exists, leaving {sheet} in place")
        _bump(status, "skipped")
        _remember(cache, sheet, outcome="skipped")
        return False

    planned.update(dest for _, dest in moves)
    for source, dest in moves:
        if dry_run:
            logger(f"[DRY RUN] {source} -> {dest}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        if cache:
            cache.moved(source, dest)
        emptied.add(source.parent)
        logger(f"[MOVED] {source} -> {dest}")

    if not dry_run:
        rewrite_sheet(sheet_dest, {track.name: track_dir / track.name for track in tracks})
        logger(f"[SHEET] {sheet_dest} now points at its tracks in {track_dir}")

    _bump(status, "roms_processed")
    return True


def process_roms(
    input_folder, logger, status, dry_run=False, rom_root=None, files=None, cache=None
):
    """
    Move ROMs from input_folder into the EmuDeck layout under rom_root
    (ES-DE's ROM folder by default). input_folder can be rom_root itself, with
    files listing what still needs organising (see library.pending_games). Single-file games go straight into <system>/.
    Games made of several files (a .cue/.gdi with its tracks, or several
    discs) are stored so ES-DE and Steam ROM Manager list each game once:

    - "shared" layout, for M3U_SYSTEMS: the files go into
      <MULTI_FILE_DIR>/<system>/<Game>/ and <system>/<Game>.m3u points at them.
      Neither ES-DE nor Steam ROM Manager looks outside the system folders.
    - "esde" layout: ES-DE folders named like the file inside them,
      <system>/<Game>.cue/ or <system>/<Game>.m3u/ with the playlist inside.
    - other systems in the "shared" layout: files stay in <system>/, one
      entry per disc, since their Steam parsers don't accept playlists.

    A file already in a system folder under rom_root that takes its file type
    keeps that system, and is organised where it is if it's in the right
    place. Otherwise a file's system comes from a DAT hash match, then its
    folder names, then its contents. Files that can't be identified without guessing are left in
    place. Existing files are never overwritten. With dry_run nothing is moved
    and the log shows where each file would go. Folders a real run empties
    inside input_folder are removed.

    With a FileCache, checksums are reused for unchanged files, files left in
    place are marked with why, and a game the app has already organised is
    reported as a duplicate even if its name differs.

    Returns a list of placed games: {"system", "title", "path", "names",
    "dat_title"}. path is what ES-DE and Steam list (a file, or a folder ES-DE
    interprets as a file); names are the ROM names to look artwork up by;
    dat_title is the matching DAT's name (also its libretro thumbnail folder).
    """
    input_folder = Path(input_folder)
    rom_root = Path(rom_root) if rom_root else esde.rom_root()
    layout = settings.get("multi_file_layout")
    if files is None:
        files = (p for p in input_folder.rglob("*") if p.is_file())
    files = sorted((Path(f) for f in files), key=lambda f: _priority_key(f, rom_root))
    library = cache.library_hashes() if cache else {}

    status["files_total"] = len(files)
    status["files_checked"] = 0

    tracks_by_sheet = {
        f: sheet_tracks(f) for f in files if f.suffix.lower() in SHEET_SUFFIXES
    }
    owned_tracks = {track for tracks in tracks_by_sheet.values() for track in tracks}

    seen_hashes = set()
    planned = set()
    emptied = set()
    placed = []
    discs_by_game = defaultdict(list)

    for index, file in enumerate(files):
        if status.get("cancel_requested"):
            logger("[STOPPED] Stopped before " + file.name, "WARNING")
            break

        status["files_checked"] = index
        status["progress"] = int(index * 100 / len(files))
        status["current_file"] = file.name
        status["current_detail"] = ""
        status["updated_at"] = time.time()

        if file.is_dir() and is_ps3_folder(file):
            _place_ps3_folder(file, rom_root, logger, status, dry_run, planned, cache, placed, emptied, input_folder)
            continue

        # Track files move together with their .cue/.gdi sheet
        if file in owned_tracks or not is_rom_candidate(file):
            continue

        tracks = tracks_by_sheet.get(file, [])
        # DATs list the track data, not the sheet text
        hashed = tracks[0] if tracks else file
        hashes = _identify(hashed, cache, _byte_progress(status, hashed, index, len(files)))
        identity = hashes["identity"]
        relative = file.relative_to(input_folder) if input_folder in file.parents else file

        in_library = library.get(identity)
        if in_library == Path(os.path.abspath(file)):
            in_library = None
        if identity in seen_hashes or in_library:
            already = f": already in your library as {in_library}" if in_library else ""
            log = game_logger(logger, _system_folder(file, rom_root), file.stem, rom_root, input_folder)
            log(f"[DUPLICATE] {file}{already}")
            _bump(status, "duplicates")
            _remember(cache, file, outcome="duplicate")
            continue

        seen_hashes.add(identity)

        dat_name, dat_system, dat_title = lookup_hashes(_dat_hashes(hashes))
        matched_by = "checksum" if dat_name else None

        # A game dropped into a system folder that takes its file type stays that system's
        chosen = _system_folder(file, rom_root)
        if chosen and not _accepts(chosen, file.suffix.lower()):
            chosen = None
        if chosen and dat_system and canonical_system(dat_system) != canonical_system(chosen):
            # The match is for another system: its name and thumbnails don't apply
            dat_name = dat_system = dat_title = matched_by = None

        family = chosen and canonical_system(chosen)
        if not dat_name and "serial" in hashes:
            # A disc's serial, read from its header, works for compressed images too
            dat_name, dat_system, dat_title = lookup_serial(hashes["serial"], family)
            matched_by = "serial" if dat_name else None

        if not dat_name:
            # Compressed, too big to read, renamed or re-dumped: try its name instead
            dat_name, dat_system, dat_title = lookup_name(file.stem, family)
            matched_by = "name" if dat_name else None

        system = chosen or dat_system or detect_system(file, allow_guess=False)
        log = game_logger(logger, system, dat_name or file.stem, rom_root, input_folder)

        if not system:
            log(
                f"[UNSORTED] {file}: couldn't tell which system this is for. "
                "Put it in a folder named after the system (e.g. ps2/) and run again."
            )
            _bump(status, "unsorted")
            status.setdefault("unsorted_files", []).append(str(relative))
            _remember(cache, file, outcome="unsorted")
            continue

        if matched_by == "checksum":
            _bump(status, "dat_matches")
        elif matched_by == "serial":
            _bump(status, "serial_matches")
        elif matched_by == "name":
            _bump(status, "name_matches")
        else:
            misses = status.setdefault("dat_misses", {})
            reason = _miss_reason(hashed, hashes)
            misses[reason] = misses.get(reason, 0) + 1
        _identified(log, matched_by, dat_title, hashes, None if matched_by else reason)

        unit = [file] + tracks
        disc = get_disc_number(file.stem) or (dat_name and get_disc_number(dat_name))

        game = {
            "system": system,
            # Arcade zips keep their short names ("sf2"); a DAT match gives the real title
            "title": clean_name(dat_name or file.stem) if system in ARCADE_SYSTEMS else dat_name or clean_name(file.stem),
            "names": [dat_name or file.stem],
            "dat_title": dat_title,
        }

        game["identity"] = identity

        if disc and system not in ARCADE_SYSTEMS:
            title = _playlist_title(dat_name or file.stem)
            discs_by_game[(system, title)].append((disc, unit, game, log))
            continue

        playlist = None
        if tracks and _uses_shared_layout(system):
            dest_dir = rom_root / MULTI_FILE_DIR / system / file.stem
            playlist = rom_root / system / f"{file.stem}.m3u"
            launch_path = playlist
        elif tracks and layout == "esde":
            dest_dir = rom_root / system / file.name
            launch_path = dest_dir
        elif tracks and system not in ARCADE_SYSTEMS:
            # Steam can't launch a playlist for this system: hide the tracks instead
            if _place_sheet_hiding_tracks(
                file, tracks, rom_root, system, log, status, dry_run, planned, cache, emptied
            ):
                placed.append({**game, "path": rom_root / system / file.name})
                _organised(cache, rom_root / system / file.name, game, dry_run, emptied, file)
            continue
        else:
            dest_dir = rom_root / system
            launch_path = dest_dir / file.name

        if _place(unit, dest_dir, log, status, dry_run, planned, playlist, cache):
            if playlist:
                entry = Path(os.path.relpath(dest_dir / file.name, playlist.parent)).as_posix()
                _write_playlist(playlist.parent, file.stem, [entry], log, dry_run)
            placed.append({**game, "path": launch_path})
            _organised(cache, dest_dir / file.name, game, dry_run, emptied, file)

    for (system, title), discs in discs_by_game.items():
        discs.sort(key=lambda d: d[0])

        if _uses_shared_layout(system):
            dest_dir = rom_root / MULTI_FILE_DIR / system / title
            playlist_dir = rom_root / system
            launch_path = playlist_dir / f"{title}.m3u"
        elif layout == "esde":
            dest_dir = playlist_dir = launch_path = rom_root / system / f"{title}.m3u"
        else:
            # The system's Steam parser can't launch playlists: one entry per disc
            for _, unit, game, log in discs:
                if len(unit) > 1:
                    placed_disc = _place_sheet_hiding_tracks(
                        unit[0], unit[1:], rom_root, system, log, status, dry_run, planned, cache, emptied
                    )
                else:
                    placed_disc = _place(unit, rom_root / system, log, status, dry_run, planned, cache=cache)
                if placed_disc:
                    placed.append({**game, "path": rom_root / system / unit[0].name})
                    _organised(cache, rom_root / system / unit[0].name, game, dry_run, emptied, unit[0])
            continue

        playlist_entries = []
        for _, unit, game, log in discs:
            if _place(unit, dest_dir, log, status, dry_run, planned, cache=cache):
                playlist_entries.append(
                    Path(os.path.relpath(dest_dir / unit[0].name, playlist_dir)).as_posix()
                )
                _organised(cache, dest_dir / unit[0].name, game, dry_run, emptied, unit[0])

        if not playlist_entries:
            continue

        _write_playlist(
            playlist_dir, title, playlist_entries, game_logger(logger, system, title, rom_root, input_folder), dry_run
        )

        first = discs[0][2]
        placed.append(
            {
                **first,
                "title": clean_name(title),
                "names": first["names"] + [title],
                "path": launch_path,
            }
        )

    if not dry_run:
        _remove_emptied_folders(emptied, input_folder)

    status["files_checked"] = len(files)
    status["progress"] = 100
    status["current_file"] = ""

    return placed


def _size(count, scale):
    """count bytes in the unit that suits scale: "512 MB" or "4.3 GB"."""
    if scale >= 1024 ** 3:
        return f"{count / 1024 ** 3:.1f} GB"
    return f"{count / 1024 ** 2:.0f} MB"


def _place_ps3_folder(folder, rom_root, logger, status, dry_run, planned, cache, placed, emptied, input_folder):
    """
    A PS3 game is a folder of thousands of files: it's placed whole in ps3/,
    never hashed, and named from its PARAM.SFO, since the folder is often
    just a title ID like "BLUS30001".
    """
    serial = ps3_serial(folder)
    dat_name, _, dat_title = lookup_serial(serial, "ps3") if serial else (None, None, None)
    if dat_name:
        _bump(status, "serial_matches")
    title = clean_name(dat_name) if dat_name else ps3_title(folder) or clean_name(folder.stem)
    game = {"system": "ps3", "title": title, "names": [dat_name or title], "dat_title": dat_title,
            "identity": f"folder:{folder.name}"}
    dest_dir = rom_root / "ps3"

    log = game_logger(logger, "ps3", dat_name or title, rom_root, input_folder)
    log(f"[IDENTIFIED] matched by serial {serial} in {dat_title}" if dat_name else "[IDENTIFIED] no DAT match: PS3 game folder")
    if _place([folder], dest_dir, log, status, dry_run, planned, cache=cache):
        placed.append({**game, "path": dest_dir / folder.name})
        _organised(cache, dest_dir / folder.name, game, dry_run, emptied, folder)


def _byte_progress(status, path, index, total):
    """Moves the progress bar while a big file is read, so a long hash doesn't look stuck."""
    size = path.stat().st_size or 1
    done = 0

    def on_bytes(count):
        nonlocal done
        done += count
        status["progress"] = int((index + done / size) * 100 / total)
        status["current_detail"] = f"checking {_size(done, size)} of {_size(size, size)}"
        status["updated_at"] = time.time()

    return on_bytes


def _organised(cache, destination, game, dry_run, emptied, source):
    """Notes a game a real run organised, so dropping it in again is spotted as a duplicate."""
    if dry_run:
        return
    if source != destination:
        emptied.add(source.parent)
    _remember(cache, destination, outcome="organised", identity=game["identity"])


def _system_folder(file, rom_root):
    """The system folder file sits in under rom_root (e.g. "snes"), if any."""
    if rom_root not in file.parents:
        return None
    parts = file.relative_to(rom_root).parts
    return parts[0] if len(parts) > 1 and parts[0] in SYSTEM_FOLDERS else None
