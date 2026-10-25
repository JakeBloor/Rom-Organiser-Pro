from urllib.parse import quote

import requests
import zipfile
import io
import shutil
from pathlib import Path

from config import DAT_DIR


class DATFetcher:
    """Fetches and manages DAT files from various sources"""

    # Libretro database commit to fetch from (master on 2026-10-25)
    DEFAULT_LIBRETRO_COMMIT = "d5e2e4d2453e3726f6c6a569b0504653eca436ff"

    # Archive folders to extract; metadat/ holds the No-Intro and Redump DATs
    LIBRETRO_DAT_PREFIXES = ("dat/", "metadat/no-intro/", "metadat/redump/")

    # FinalBurn Neo's arcade DATs: arcade zip names ("sf2") and their titles
    DEFAULT_FBNEO_COMMIT = "2b0c1c0679df115cada7df9199ea2762222e58fd"
    FBNEO_DATS = (
        "FinalBurn Neo (ClrMame Pro XML, Arcade only).dat",
        "FinalBurn Neo (ClrMame Pro XML, Neogeo only).dat",
    )

    def __init__(self, logger):
        self.logger = logger
        DAT_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_libretro_repo(self, commit_hash=None):
        """
        Download libretro-database archive
        and extract DAT files.
        """
        try:
            commit = commit_hash or self.DEFAULT_LIBRETRO_COMMIT
            libretro_dir = DAT_DIR / "libretro"
            commit_marker = libretro_dir / ".commit"

            if (
                commit_marker.exists()
                and commit_marker.read_text().strip() == commit
                and any(libretro_dir.rglob("*.dat"))
            ):
                self.logger(
                    f"libretro DATs for {commit[:7]} already present, skipping download",
                    "INFO",
                )
                return True

            zip_url = (
                "https://github.com/libretro/" f"libretro-database/archive/{commit}.zip"
            )

            self.logger(
                f"Fetching libretro database archive: {zip_url}",
                "INFO",
            )

            response = requests.get(
                zip_url,
                timeout=60,
                stream=True,
            )

            response.raise_for_status()

            content = response.content

            if not content.startswith(b"PK"):
                self.logger(
                    "Downloaded libretro archive is not a ZIP file",
                    "ERROR",
                )
                return False

            # Extract into a staging folder and only replace the existing DATs
            # once extraction succeeds, so a failed download keeps what's on disk
            staging_dir = DAT_DIR / "libretro.partial"
            if staging_dir.exists():
                shutil.rmtree(staging_dir)

            extracted = 0

            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for name in zf.namelist():
                    # Strip the "libretro-database-<commit>/" root folder
                    relative = Path(*Path(name.replace("\\", "/")).parts[1:])

                    if relative.suffix.lower() != ".dat" or not any(
                        relative.as_posix().lower().startswith(prefix)
                        for prefix in self.LIBRETRO_DAT_PREFIXES
                    ):
                        continue

                    # Any failure abandons the whole download (handled
                    # below), so a half-extracted set never replaces old DATs
                    dest = staging_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(zf.read(name))
                    extracted += 1
                    self.logger(
                        f"Extracted DAT: {relative}",
                        "SUCCESS",
                    )

            if not extracted:
                shutil.rmtree(staging_dir, ignore_errors=True)
                self.logger(
                    "No .dat files found in libretro archive dat/ or metadat/ directories",
                    "WARNING",
                )
                return False

            (staging_dir / ".commit").write_text(commit)

            if libretro_dir.exists():
                shutil.rmtree(libretro_dir)
                self.logger(
                    f"Replaced previous libretro DATs in {libretro_dir}",
                    "INFO",
                )

            staging_dir.rename(libretro_dir)

            return True

        except requests.exceptions.RequestException as e:
            self.logger(
                f"Failed to download libretro archive: {e}",
                "ERROR",
            )
            return False

        except Exception as e:
            self.logger(
                f"Error extracting libretro archive: {e}",
                "ERROR",
            )
            return False

    def fetch_fbneo_dats(self, commit_hash=None):
        """
        Download FinalBurn Neo's arcade and Neo Geo DATs into dats/fbneo/,
        skipping the download while that commit's files are already there.
        """
        commit = commit_hash or self.DEFAULT_FBNEO_COMMIT
        fbneo_dir = DAT_DIR / "fbneo"
        marker = fbneo_dir / ".commit"

        if (
            marker.exists()
            and marker.read_text().strip() == commit
            and all((fbneo_dir / name).exists() for name in self.FBNEO_DATS)
        ):
            self.logger(f"FinalBurn Neo DATs for {commit[:7]} already present, skipping download")
            return True

        # Downloaded into a staging folder so a failure keeps the DATs on disk
        staging_dir = DAT_DIR / "fbneo.partial"
        shutil.rmtree(staging_dir, ignore_errors=True)
        staging_dir.mkdir(parents=True)

        try:
            for name in self.FBNEO_DATS:
                url = f"https://raw.githubusercontent.com/libretro/FBNeo/{commit}/dats/{quote(name)}"
                self.logger(f"Fetching {name}")
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                (staging_dir / name).write_bytes(response.content)
        except requests.exceptions.RequestException as e:
            shutil.rmtree(staging_dir, ignore_errors=True)
            self.logger(f"Failed to download FinalBurn Neo DATs: {e}", "ERROR")
            return False

        marker_file = staging_dir / ".commit"
        marker_file.write_text(commit)
        shutil.rmtree(fbneo_dir, ignore_errors=True)
        staging_dir.rename(fbneo_dir)
        self.logger("FinalBurn Neo DATs downloaded", "SUCCESS")
        return True

    def fetch_libretro_dats(self, commit_hash=None):
        """
        High-level convenience wrapper.
        """
        success = self.fetch_libretro_repo(commit_hash)

        return {"libretro": bool(success)}
