import requests
import zipfile
import io
import shutil
from pathlib import Path

from config import DAT_DIR


class DATFetcher:
    """Fetches and manages DAT files from various sources"""

    # Libretro database commit to fetch from
    DEFAULT_LIBRETRO_COMMIT = "559696d00979f4f3c593a1ee2c7aef0ed4c47695"

    # Archive folders to extract; metadat/ holds the No-Intro and Redump DATs
    LIBRETRO_DAT_PREFIXES = ("dat/", "metadat/no-intro/", "metadat/redump/")

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

    def fetch_libretro_dats(self, commit_hash=None):
        """
        High-level convenience wrapper.
        """
        success = self.fetch_libretro_repo(commit_hash)

        return {"libretro": bool(success)}
