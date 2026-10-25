Feature: Downloading images for ES-DE and Steam

  Scenario: Every image type is filled from libretro and SteamGridDB
    Given libretro has "Named_Boxarts, Named_Snaps, Named_Titles" for "Chrono Trigger (USA)" in "Nintendo - Super Nintendo Entertainment System"
    And SteamGridDB has every kind of image for its game
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)" from the DAT "Nintendo - Super Nintendo Entertainment System"
    Then the saved media should be "covers, screenshots, titlescreens, marquees, fanart, steam_tall, steam_long, steam_hero, steam_logo, steam_icon"
    And the ES-DE "covers" image should come from libretro
    And the ES-DE "marquees" image should come from SteamGridDB "logos"
    And the ES-DE "fanart" image should come from SteamGridDB "heroes"
    And the Steam "long" image should come from SteamGridDB "grids" sized "920x430,460x215"
    And the Steam "tall" image should be saved for "Chrono Trigger (USA)"

  Scenario: Without a DAT match the system's libretro folder and the game's other names are tried
    Given libretro has "Named_Boxarts" for "Final Fantasy VII (USA)" in "Sony - PlayStation"
    And SteamGridDB is disabled
    When artwork is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1), Final Fantasy VII (USA)"
    Then the saved media should be "covers"
    And the ES-DE "covers" image should be saved for "Final Fantasy VII (USA)"

  Scenario: Characters libretro can't use in file names are replaced
    Given libretro has "Named_Boxarts" for "Q_bert's Qubes (USA)" in "Atari - 2600"
    And SteamGridDB is disabled
    When artwork is fetched for "atari2600/Q-bert's Qubes (USA).a26" named "Q*bert's Qubes (USA)" from the DAT "Atari - 2600"
    Then the saved media should be "covers"

  Scenario: SteamGridDB fills the cover when libretro can't be reached
    Given libretro can't be reached
    And SteamGridDB has every kind of image for its game
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)" from the DAT "Nintendo - Super Nintendo Entertainment System"
    Then the ES-DE "covers" image should come from SteamGridDB "grids"
    And the artwork log should mention "[ARTWORK ERROR] libretro thumbnails"

  Scenario: Systems libretro doesn't cover go straight to SteamGridDB
    Given SteamGridDB has every kind of image for its game
    When artwork is fetched for "ports/Doom.sh" named "Doom"
    Then libretro should not be asked
    And the saved media should be "covers, marquees, fanart, steam_tall, steam_long, steam_hero, steam_logo, steam_icon"

  Scenario: Images a game already has are never downloaded again
    Given SteamGridDB has every kind of image for its game
    And "snes/Chrono Trigger (USA).sfc" already has every image
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)" from the DAT "Nintendo - Super Nintendo Entertainment System"
    Then nothing should be requested
    And the saved media should be nothing

  Scenario Outline: SteamGridDB problems are reported, not raised
    Given libretro thumbnails are disabled
    And SteamGridDB <situation>
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)"
    Then the saved media should be nothing
    And the artwork log should mention "<message>"

    Examples:
      | situation                  | message                                       |
      | has no API key             | Missing SteamGridDB API key                   |
      | finds no game              | No results for Chrono Trigger                 |
      | has no images for the game | No SteamGridDB images found for Chrono Trigger |
      | can't be reached           | [ARTWORK ERROR] Chrono Trigger                |

  Scenario: Nothing is downloaded when both sources are turned off
    Given libretro thumbnails are disabled
    And SteamGridDB is disabled
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)"
    Then nothing should be requested

  Scenario: JPEG images keep their extension
    Given libretro thumbnails are disabled
    And SteamGridDB has every kind of image for its game as JPEG
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)"
    Then the Steam "tall" image should be saved for "Chrono Trigger (USA)" as ".jpg"

  Scenario: A game that already has its Steam artwork still gets its ES-DE images
    Given libretro thumbnails are disabled
    And SteamGridDB has every kind of image for its game
    And "snes/Chrono Trigger (USA).sfc" already has its Steam artwork
    When artwork is fetched for "snes/Chrono Trigger (USA).sfc" named "Chrono Trigger (USA)"
    Then the saved media should be "covers, marquees, fanart"

  Scenario: Each download worker reuses one connection
    Given connections are counted
    When two images are requested on this thread
    Then 1 connection should have been opened

  Scenario: Games in an alternative folder get the libretro thumbnails of the system it stands for
    Given libretro has "Named_Boxarts" for "Sonic the Hedgehog 2 (World)" in "Sega - Mega Drive - Genesis"
    And SteamGridDB is disabled
    When artwork is fetched for "megadrive/Sonic the Hedgehog 2 (World).md" named "Sonic the Hedgehog 2 (World)"
    Then the saved media should be "covers"
