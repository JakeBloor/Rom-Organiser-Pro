# ROM Organizer Pro documentation

ROM Organizer Pro is a small web app that sorts retro game ROMs into the folders EmuDeck uses on the Steam Deck. It also downloads game data and artwork so each game looks right in both places you play it:

- in **ES-DE**, EmuDeck's game launcher, and
- in your **Steam library**, through Steam ROM Manager.

You give it a folder of new ROMs. It works out which system each file is for, moves it into the right system folder, and fetches covers, screenshots, logos and the rest. A dry run shows you where everything would go before anything moves.

## Guides

| Guide | Read it to |
|---|---|
| [Getting started](getting-started.md) | Install the app, run it and organise your first ROMs |
| [Using the app](using-the-app.md) | Learn what each part of the page does: scanning, dry runs, progress and reports |
| [How games are stored](how-games-are-stored.md) | See where files go, including multi-disc games, and why |
| [Game data and artwork](artwork.md) | See which images are downloaded, where they come from and how Steam uses them |
| [How systems are detected](detection.md) | Understand how the app decides a file is for the SNES, the PS2 or another system |
| [Configuration](configuration.md) | Change folders, accounts, the port and the storage layout on the Settings page |
| [Web API](api.md) | Call the app from scripts |
| [Development](development.md) | Find your way around the code and run the tests |
| [Troubleshooting](troubleshooting.md) | Fix common problems |

## At a glance

- **Never overwrites.** If a file already exists at the destination, the new one stays where it was and the log says why.
- **Never guesses when moving files.** If it can't tell the system for certain, the file stays in your import folder, marked as unsorted.
- **Matches games against DAT files.** The No-Intro and Redump game lists identify each ROM by its checksum. That gives it the correct system and the official game name, which artwork lookups use.
- **Lists each game once in both ES-DE and Steam,** including multi-disc games.
