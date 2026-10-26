"""
Videos and manuals from EmuMovies (emumovies.com), the first source asked
for each game.

Supporters can download from EmuMovies' file server over FTP, using the
login shown under "FTP Login" on the site. The server groups media by kind,
then by set: "Official/Video Snaps (HQ)/Sony Playstation (Video Snaps)
(HQ480p)(ReDump)(EM 2.3)/<game>.mp4", "Official/Game Manuals/.../<game>.pdf".
Files are named the No-Intro/Redump way, which is how games are matched.
Artwork is only offered as whole-system archive packs, so images come from
the other sources.

The connection is read-only: it can list folders and download files, and
nothing else, so nothing on EmuMovies' server is ever changed or deleted.
Folder listings are cached for a day, and one connection is used at a time.
"""

import ftplib
import json
import os
import re
import shutil
import ssl
import tempfile
import time
from pathlib import Path

from config import DAT_SYSTEM_IDS, canonical_system
from modules import settings
from modules.dat_validation import name_key
from modules.media import ESDE_MEDIA_TYPES, esde_media_path, has_esde_media

LISTING_CACHE = Path(__file__).resolve().parent.parent / "cache" / "emumovies.json"
LISTING_TTL_SECONDS = 24 * 60 * 60

OFFICIAL = "Official"
VIDEO_FOLDERS = {"HD": "Video Snaps (HD)", "HQ": "Video Snaps (HQ)", "SQ": "Video Snaps (SQ)"}
MANUAL_FOLDER = "Game Manuals"
# Words after a set's system name that don't change the system:
# "Sega Genesis - USA", "Sony Playstation 3 - PSN", "Nintendo Wii U eShop"
SET_QUALIFIERS = {
    "usa", "europe", "japan", "other", "psn", "retail", "xbla", "eshop",
    "hacks", "homebrew", "translations",
}
# Sets searched last, since they're mostly not original releases
EXTRA_SET_REGEX = re.compile(r"hack|homebrew|translation|extras", re.I)

# EmuMovies' names for systems, besides those made from their DAT names
# ("Sony - PlayStation" -> "Sony PlayStation", "PlayStation")
SYSTEM_NAMES = {
    "nes": ("Nintendo NES", "Nintendo Entertainment System"),
    "snes": ("Nintendo Super Nintendo", "Super Nintendo Entertainment System", "Super Nintendo"),
    "gba": ("Nintendo GBA",),
    "gbc": ("Nintendo Gameboy Color",),
    "psp": ("Sony PSP", "Sony PlayStation Portable"),
    "genesis": ("Sega Genesis", "Sega Mega Drive", "Sega Genesis - Mega Drive"),
    "xbox": ("Microsoft XBOX",),
    "wiiu": ("Nintendo WiiU",),
    "neogeo": ("SNK Neo Geo AES", "SNK Neo Geo MVS", "SNK Neo-Geo MVS"),
    "arcade": ("MAME Arcade", "MAME"),
    "mame": ("MAME Arcade", "MAME"),
    "fbneo": ("MAME Arcade", "MAME"),
}

# What the artwork packs fill, in the order they're tried
ARTWORK_TYPES = ("covers", "3dboxes", "backcovers", "screenshots", "titlescreens", "marquees",
                 "physicalmedia", "fanart")

REGION_REGEX = re.compile(r"\(([^)]*(?:USA|Europe|Japan|World|Asia|Korea|Australia)[^)]*)\)")


class ReadOnlyFTP:
    """
    An FTP connection that can only list folders and download files. Any
    other command (deleting, uploading, renaming, making folders) is refused
    here, before it reaches EmuMovies' server.
    """

    ALLOWED = {"nlst", "size", "quit", "close"}

    def __init__(self, ftp):
        self._ftp = ftp

    def __getattr__(self, name):
        if name in self.ALLOWED:
            return getattr(self._ftp, name)
        raise PermissionError(f"The EmuMovies connection is read-only: {name} isn't allowed")

    def retrbinary(self, command, callback):
        if not command.startswith("RETR "):
            raise PermissionError(f"The EmuMovies connection is read-only: {command.split()[0]} isn't allowed")
        return self._ftp.retrbinary(command, callback)


def _norm(name):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def _base_title(name):
    """"Chrono Trigger (USA) (Rev 1)" -> "chrono trigger"."""
    return name_key(re.split(r"\s*[\(\[]", name, maxsplit=1)[0])


def set_system_name(set_name):
    """
    The system name a set folder is for, normalised: "Sega Genesis - USA
    (Video Snaps)(HQ)(No-Intro)(EM 2.6)" -> "sega genesis".
    """
    words = _norm(set_name.split("(", 1)[0]).split()
    while words and words[-1] in SET_QUALIFIERS:
        words.pop()
    return " ".join(words)


def system_names(system):
    """Every name a system's EmuMovies sets might have, normalised."""
    system = canonical_system(system)
    names = set(SYSTEM_NAMES.get(system, ()))
    for dat_name, dat_system in DAT_SYSTEM_IDS.items():
        if dat_system == system:
            names.add(dat_name.replace(" - ", " "))
            names.add(dat_name.split(" - ", 1)[-1])
    return {_norm(name) for name in names}


def match_file(files, game):
    """
    The file for game: by its DAT name or file name, else by its title
    without tags, preferring its region. None if there isn't one.
    """
    by_name = {name_key(Path(f).stem): f for f in files}
    names = list(game["names"]) + [Path(game["path"]).stem]
    for name in names:
        found = by_name.get(name_key(name))
        if found:
            return found

    base = _base_title(names[0])
    candidates = sorted(f for f in files if _base_title(Path(f).stem) == base)
    if not candidates:
        return None
    region = REGION_REGEX.search(names[0])
    if region:
        regional = [f for f in candidates if f"({region.group(1)})" in f]
        if regional:
            return regional[0]
    return candidates[0]


def wanted_kinds():
    """(ES-DE media type, server folders to look in, in order) for what's switched on."""
    kinds = []
    if settings.get("emumovies_videos"):
        quality = settings.get("emumovies_video_quality")
        order = [quality] + [q for q in ("HQ", "SQ", "HD") if q != quality]
        kinds.append(("videos", [VIDEO_FOLDERS[q] for q in order]))
    if settings.get("emumovies_manuals"):
        kinds.append(("manuals", [MANUAL_FOLDER]))
    return kinds


class EmuMoviesServer:
    """One read-only FTP connection to EmuMovies' file server, with cached folder listings."""

    def __init__(self, host, user, password, logger, cache_path=None):
        self.host = host
        self.user = user
        self.password = password
        self.logger = logger
        self.cache_path = Path(cache_path or LISTING_CACHE)
        self.ftp = None
        self.sets = {}
        try:
            self.listings = json.loads(self.cache_path.read_text())
        except (OSError, ValueError):
            self.listings = {}

    def connect(self):
        """Logs in, encrypted if the server allows it, as EmuMovies' FAQ suggests trying first."""
        ftp = ftplib.FTP_TLS(self.host, timeout=30)
        try:
            ftp.login(self.user, self.password)
            ftp.prot_p()
        except (ssl.SSLError, ftplib.error_perm, ftplib.error_reply):
            ftp.close()
            ftp = ftplib.FTP(self.host, timeout=30)
            ftp.login(self.user, self.password)
        self.ftp = ReadOnlyFTP(ftp)

    def close(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except (OSError, ftplib.Error):
                pass
            self.ftp = None
        self.save()

    def save(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.listings))

    def listing(self, path):
        """The names in a server folder, reused from the cache for a day."""
        cached = self.listings.get(path)
        if cached and time.time() - cached["listed"] < LISTING_TTL_SECONDS:
            return cached["names"]
        try:
            names = sorted(Path(name).name for name in self.ftp.nlst(path))
        except ftplib.error_perm:
            names = []
        self.listings[path] = {"names": names, "listed": time.time()}
        return names

    def system_sets(self, folder, system):
        """
        The sets in a media folder (e.g. "Video Snaps (HQ)") for a system,
        original releases first, hacks, homebrew and extras last.
        """
        key = (folder, canonical_system(system))
        if key not in self.sets:
            wanted = system_names(system)
            found = [
                name for name in self.listing(f"{OFFICIAL}/{folder}")
                if set_system_name(name) in wanted
            ]
            found.sort(key=lambda name: (bool(EXTRA_SET_REGEX.search(name)), name))
            self.sets[key] = [f"{OFFICIAL}/{folder}/{name}" for name in found]
        return self.sets[key]

    def download(self, remote, destination, on_bytes=None):
        """
        Copies remote down to destination through a temporary file, so a
        failure leaves nothing half written. on_bytes gets each block's size.
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".emumovies-")
        try:
            with os.fdopen(fd, "wb") as file:
                def write(block):
                    file.write(block)
                    if on_bytes:
                        on_bytes(len(block))

                self.ftp.retrbinary(f"RETR {remote}", write)
            os.replace(temporary, destination)
        except BaseException:
            os.unlink(temporary)
            raise


def _find(server, game, media_type, folders):
    """The server path of game's file of media_type, searching the folders' sets in order."""
    usable = ESDE_MEDIA_TYPES[media_type]
    for folder in folders:
        for set_path in server.system_sets(folder, game["system"]):
            files = [f for f in server.listing(set_path) if Path(f).suffix.lower() in usable]
            found = match_file(files, game)
            if found:
                return f"{set_path}/{found}"
    return None


def _link_or_copy(source, destination):
    """A hard link saves space when the library shares a drive with ES-DE's media; else a copy."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def fetch_emumovies(game, media_root, server, logger, library=None):
    """
    Fills the images game is missing from the EmuMovies artwork library, and
    downloads its video and manual when connected. Either may be None.
    Returns the media types saved. Never replaces media already there.
    """
    saved = []
    for media_type in ARTWORK_TYPES if library else ():
        if has_esde_media(media_root, game["system"], game["path"], media_type):
            continue
        image = library.find(game, media_type)
        if image:
            _link_or_copy(
                image, esde_media_path(media_root, game["system"], game["path"], media_type, image.suffix.lower())
            )
            saved.append(media_type)

    for media_type, folders in wanted_kinds() if server else ():
        if has_esde_media(media_root, game["system"], game["path"], media_type):
            continue
        remote = _find(server, game, media_type, folders)
        if not remote:
            continue
        destination = esde_media_path(
            media_root, game["system"], game["path"], media_type, Path(remote).suffix.lower()
        )
        try:
            server.download(remote, destination)
        except (OSError, ftplib.Error) as e:
            logger(f"[EMUMOVIES ERROR] {game['system']} · {game['names'][0]} · {Path(remote).name}: {e}", "WARNING")
            continue
        saved.append(media_type)

    if saved:
        logger(f"[EMUMOVIES] {game['system']} · {game['names'][0]} · {', '.join(saved)}")
    return saved


def connect(logger):
    """A logged-in, read-only EmuMovies connection, or None when it's off, not set up, or can't be reached."""
    if not settings.get("enable_emumovies"):
        return None

    hosts = [h for h in (settings.get("emumovies_host_main"), settings.get("emumovies_host_backup")) if h]
    user = settings.get("emumovies_user")
    password = settings.get("emumovies_password")
    if not (hosts and user and password):
        logger("[EMUMOVIES] Add your FTP server, user name and password in Settings", "WARNING")
        return None

    # The backup server is tried when the main one can't be reached or refuses the login
    for host in hosts:
        server = EmuMoviesServer(host, user, password, logger)
        try:
            server.connect()
        except (OSError, ftplib.Error) as e:
            logger(f"[EMUMOVIES ERROR] Couldn't log in to {host}: {e}", "WARNING")
            continue
        return server
    return None
