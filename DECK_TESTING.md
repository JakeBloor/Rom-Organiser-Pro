# ROM Organizer Pro: testing on the Steam Deck

Context for a Claude Code session running on the Steam Deck. The app was built and tested on a Mac, with every external service faked in the tests. This session's job is to try it on the real Deck: its library, SD card, ES-DE, Steam ROM Manager and network. It should fix what breaks and report back what works.

Read [docs/README.md](docs/README.md) for what the app does, and [docs/development.md](docs/development.md) for how the code fits together.

## Starting a session on the Deck

In Desktop Mode, open a terminal in the repo, run `git pull`, start Claude Code, and paste:

```
Read DECK_TESTING.md, then docs/README.md and docs/development.md, so you know
this project and how it's built.

We're testing ROM Organizer Pro on my Steam Deck for the first time. Set it up
(venv, requirements, start the app), then work through the DECK_TESTING.md
checklist with me, one section at a time.

- Start with a dry run and don't move any files until I say so.
- For each check, tell me what to look at and wait for my answer before moving on.
- If something breaks, find the cause, fix it with a test (coverage must stay
  at 100%), and tell me what you changed.
- Never ask for, print or commit my account details: I'll enter them on the
  Settings page myself.
- Before downloading EmuMovies artwork packs, check free space and tell me how
  much they'll need.
- Keep a list of what passed, what failed and what you fixed, and don't commit
  until I ask.
```

## What the app is

A Flask web app that organises retro game ROMs for EmuDeck on the Steam Deck, so each game shows exactly once in **ES-DE** and in **Steam**, through Steam ROM Manager, with artwork, videos and manuals.

A run has five steps:

1. **Find new games** in the ROM folder.
2. **Organise them.** Each game is identified by DAT checksum, then disc serial, then name, then moved into place or organised where it is.
3. **EmuMovies:** images from local artwork packs, plus videos and manuals from EmuMovies' FTP.
4. **Skyscraper and ScreenScraper:** game data and any media still missing.
5. **libretro thumbnails and SteamGridDB:** any media still missing, plus Steam artwork.

The page polls `/status` every second for live progress. Organising is the critical part: everything after it only adds media and never moves files.

## Set up on the Deck

```bash
cd ~/RomOrganiser            # wherever the repo is cloned
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py                # then open http://127.0.0.1:8181 in Desktop Mode
```

- **Account details:** `settings.local.json` is git-ignored, so it isn't on the Deck after a pull. Ask the user to enter their accounts on the **⚙️ Settings** page, or to create the file themselves. The accounts are the EmuMovies FTP main and backup server, user name and password; the SteamGridDB API key; and the ScreenScraper user name and password. Never ask for these values in chat, never print them, and never commit the file.
- **Other settings:** `settings.json` is in git and holds every other setting. The defaults expect `~/ES-DE`, with the ROM and media folders read from ES-DE's own settings file.
- **On first start** the app downloads the libretro DATs (several hundred MB) and FinalBurn Neo's arcade DATs into `dats/`, both git-ignored.

## Rules for this project

- **Tests:** `pytest --cov` must stay at **100% branch coverage**. The tests are pytest-bdd: a feature file per area in `tests/features/` and step code in `tests/steps/`. Every fix needs a scenario.
- **Never overwrite or lose the user's files.** The organiser never overwrites anything. It only removes folders a run emptied, never system folders, and only replaces a playlist whose every entry is the same game's own files.
- **EmuMovies is read-only.** `ReadOnlyFTP` in `modules/emumovies.py` only allows login, `NLST`, `SIZE`, `RETR`, `QUIT` and close. Don't add anything that could change their server. The only files ever deleted are the app's own downloaded archives on the Deck.
- **Keep secrets out of output and git.** Mask hosts, user names and passwords in anything printed (see the folder-listing check below).
- **Run Python under `.venv/bin/python`.** Test runs must not touch the real `cache/` or `settings.local.json`; `tests/conftest.py` already isolates both.
- **Commits:** commit to `main` and push only when the user asks. End commit messages with the `Co-Authored-By` line the session gives you.

## What's untested on real hardware

Work through these with the user, roughly in this order. Note what happens with each, fix what breaks, and add a test for every fix.

### 1. The basics

- [ ] **The app starts.** The page loads in Firefox in Desktop Mode. The page has never been looked at in a real browser: check the charts, the New games panel, the Settings page, the Stop button, and light and dark mode.
- [ ] **libarchive is available.** Artwork packs need it. Run `python -c "import ctypes.util; print(ctypes.util.find_library('archive'))"`, which should print a path. SteamOS's package manager uses libarchive, so it should be there. If it isn't, `modules/unpack.py` raises a clear `UnpackError`, and an alternative would be needed. RARLAB's `unrar` binary was considered but not used.
- [ ] **The DATs download** on first start, and the startup log says how many entries loaded.

### 2. Organising (use Dry run first)

- [ ] **Dry run on the real library.** The first run treats every existing game as new and works through the whole library once. Compressed and big images are only fingerprinted, about 3 MB each, so this should be minutes, not hours. Watch the progress line for anything that stalls.
- [ ] **DAT matches.** An earlier run matched 325 of about 3,000 ROMs. Checksum, serial and name matching have been added since, and the run report's "DAT matches" chart shows the counts by method and the reasons for misses. Report the new numbers.
- [ ] **A real run,** then check ES-DE and Steam for **duplicate games**. These were the last bug fixed, and the fix was reproduced on test data, not the user's library:
  - a `.cue` naming its track with different capitals
  - a playlist the user made themselves
  - discs appended to an old playlist
  - loose `.cue`/`.bin` pairs for 3DO and PC Engine CD
- [ ] **Multi-disc games** in the shared layout get `psx/Game.m3u` with entries like `../.multifile/psx/Game/Game (Disc 1).chd`. Launch one in DuckStation or RetroArch, from ES-DE and from Steam, and change disc.
- [ ] **3DO and PC Engine CD:** the `.cue` stays in the system folder and is rewritten to point at its tracks in `../.multifile/...`. Launch one; Beetle PCE and Opera should follow the relative path, but this hasn't been tried.
- [ ] **PS3 game folders** (`Game.ps3/`, or folders holding `PS3_GAME/`) count as one game, titled from `PARAM.SFO`, and are never looked inside.
- [ ] **New games dropped in:** drop a few into their system folders, check the New games panel picks them up within 30 seconds, then organise. **Re-organise everything** should work through the library again without moving anything already in place.

### 3. EmuMovies (the user is a supporter)

- [ ] **The connection** from the Deck's network: some networks block FTP. It tries encrypted FTP first, then plain FTP, then the backup server.
- [ ] **Videos and manuals** download during an organise run, and play or open in ES-DE.
- [ ] **Artwork packs:** **Download EmuMovies artwork**, on the home page. This is big: about 37 GB for 12 popular systems, roughly 1 to 10 GB each, at about 7.6 MB/s measured from the Mac.
  - Check free space first, especially on the SD card.
  - Packs unpack into `emumovies-artwork/` next to ES-DE's media folder.
  - Then check the downloaded parts are deleted, `manifest.json` is written, and an organise run fills images from the library.
  - Images are hard-linked when the library and ES-DE's media share a drive, and copied otherwise; check which happened.
- [ ] **Matching:** some community packs name games differently, so note systems where few images match.

### 4. Other sources and Steam

- [ ] **Skyscraper, if installed:** it should only fill gaps. Its generate step passes `skipexisting*` flags so it never overwrites EmuMovies media.
- [ ] **SteamGridDB** Steam artwork and libretro thumbnails.
- [ ] **Steam ROM Manager:** click **Use this app's artwork in Steam ROM Manager**. It backs up `userConfigurations.json` as `.rom-organiser.bak` first. Then in SRM choose Parse, then Save to Steam, and check the artwork and that there are no duplicates.

## Useful commands

```bash
.venv/bin/python -m pytest -q --cov          # all tests, must report 100%
tail -f logs/rom_organiser_*.log              # the app's log; every game line reads "[TAG] system · game · ..."
```

To check EmuMovies' folders from the Deck: read-only, and printing folder names only, with secrets masked:

```bash
.venv/bin/python - <<'PY'
from modules import settings, emumovies
secrets = [settings.get(k) for k in ("emumovies_host_main", "emumovies_host_backup", "emumovies_user", "emumovies_password") if settings.get(k)]
def mask(text):
    for secret in secrets:
        text = text.replace(secret, "<hidden>")
    return text
server = emumovies.connect(lambda m, l="INFO": print(mask(str(m))))
print("connected:", server is not None)
if server:
    print(server.listing("Official"))
    server.close()
PY
```

## Known loose ends

- **Out-of-date docs:** `readme.md` and `GETTING_STARTED.md` at the top level are outdated (wrong port, environment variables). `docs/` is current.
- **Test logs:** the tests write log files into the real `logs/` folder. This is harmless but clutters it.
- **Old secrets in git history:** the old SteamGridDB key and ScreenScraper password are still in the repo's history, from `config.py` and an earlier `settings.json`. The user said they'd rotate them.
- **3D boxes and physical media** come only from EmuMovies packs or Skyscraper. **Miximages** are made by ES-DE itself.
- **No audio:** audio and music from EmuMovies are deliberately left out.
