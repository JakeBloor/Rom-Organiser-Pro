Feature: EmuMovies artwork packs, kept as a local library

  Scenario: The best pack of each art type is chosen
    Given a system's artwork files
      | file                                                                        |
      | Sony Playstation (Boxes-2D)(ReDump)(EM 2.2).part1.rar                       |
      | Sony Playstation (Boxes-2D)(ReDump)(EM 2.2).part2.rar                       |
      | Sony Playstation (Boxes-2D)(ReDump)(EM 2.1).rar                             |
      | Sony Playstation (2D Boxes)(WallyWonka 1.1).rar                             |
      | Sony PlayStation - Japan (2D Boxes)(Robin55 1.0).rar                        |
      | Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part10.rar                      |
      | Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part2.rar                       |
      | Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part1.rar                       |
      | Nintendo 64 (3D Boxes)(EM 20160611).rar                                     |
      | Sony Playstation (Backgrounds-Game)(ReDump)(EM 2.4).7z.002                  |
      | Sony Playstation (Backgrounds-Game)(ReDump)(EM 2.4).7z.001                  |
      | Sony Playstation (Snaps-Title)(ReDump)(EM 2.3).zip                          |
      | Sony Playstation (Boxes-Spines)(ReDump)(EM 2.2).rar                         |
      | Sony Playstation (Custom Marquees)(NinjasDojo 1.0).rar                      |
      | Sony Playstation Readme.txt                                                 |
    When the packs are chosen
    Then the chosen packs should be
      | media type   | pack                                                 | parts                                                                                                                                                                  |
      | covers       | Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)          | Sony Playstation (Boxes-2D)(ReDump)(EM 2.2).part1.rar, Sony Playstation (Boxes-2D)(ReDump)(EM 2.2).part2.rar                                                          |
      | 3dboxes      | Sony Playstation (Boxes-3D)(ReDump)(EM 2.2)          | Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part1.rar, Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part2.rar, Sony Playstation (Boxes-3D)(ReDump)(EM 2.2).part10.rar |
      | fanart       | Sony Playstation (Backgrounds-Game)(ReDump)(EM 2.4)  | Sony Playstation (Backgrounds-Game)(ReDump)(EM 2.4).7z.001, Sony Playstation (Backgrounds-Game)(ReDump)(EM 2.4).7z.002                                              |
      | titlescreens | Sony Playstation (Snaps-Title)(ReDump)(EM 2.3)       | Sony Playstation (Snaps-Title)(ReDump)(EM 2.3).zip                                                                                                                     |

  Scenario: An official pack dated the old way loses to a numbered one
    Given a system's artwork files
      | file                                                   |
      | Nintendo 64 (3D Boxes)(EM 20160611).rar                |
      | Nintendo 64 (3D Boxes)(No-Intro 20210322)(EM 3.0).rar  |
    When the packs are chosen
    Then the "3dboxes" pack should be "Nintendo 64 (3D Boxes)(No-Intro 20210322)(EM 3.0)"

  Scenario: Packs are downloaded, unpacked flat into the library, and their parts deleted
    Given a ROM folder with "psx" and "snes" games
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" in 2 parts holding "Final Fantasy VII (USA) (Disc 1).png, Spyro the Dragon (USA).png, readme.txt"
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Snaps-Title)(ReDump)(EM 2.3)" in 1 part holding "Spyro the Dragon (USA).png"
    When the artwork packs are downloaded
    Then the library should hold "psx/covers/Final Fantasy VII (USA) (Disc 1).png, psx/covers/Spyro the Dragon (USA).png, psx/titlescreens/Spyro the Dragon (USA).png"
    And the manifest should say "psx/covers" came from "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" with 2 images
    And no downloaded parts or unpacking folders should be left
    And the pack summary should be 2 installed, 0 up to date and 0 failed
    And the pack log should mention "snes · No artwork packs on EmuMovies"
    And nothing on the EmuMovies server should have been changed by the packs

  Scenario: Packs already unpacked aren't downloaded again
    Given a ROM folder with "psx" and "snes" games
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" in 1 part holding "Spyro the Dragon (USA).png"
    And the artwork packs have been downloaded
    When the artwork packs are downloaded
    Then the pack summary should be 0 installed, 1 up to date and 0 failed

  Scenario: A newer version of a pack replaces the old one
    Given a ROM folder with "psx" and "snes" games
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.1)" in 1 part holding "Old Game (USA).png"
    And the artwork packs have been downloaded
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" in 1 part holding "New Game (USA).png"
    When the artwork packs are downloaded
    Then the library should hold "psx/covers/New Game (USA).png"
    And the manifest should say "psx/covers" came from "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" with 1 images

  Scenario Outline: A pack that can't be downloaded or unpacked is skipped and cleaned up
    Given a ROM folder with "psx" and "snes" games
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" in 1 part holding "Spyro the Dragon (USA).png"
    And <problem>
    When the artwork packs are downloaded
    Then the pack summary should be 0 installed, 0 up to date and 1 failed
    And the pack log should mention "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)"
    And no downloaded parts or unpacking folders should be left

    Examples:
      | problem                              |
      | EmuMovies pack downloads fail        |
      | the pack on EmuMovies is damaged     |

  Scenario: A stop request ends the pack downloads before the next pack
    Given a ROM folder with "psx" and "snes" games
    And EmuMovies has the "Sony Playstation" pack "Sony Playstation (Boxes-2D)(ReDump)(EM 2.2)" in 1 part holding "Spyro the Dragon (USA).png"
    When the artwork packs are downloaded after a stop request
    Then the pack summary should be 0 installed, 0 up to date and 0 failed

  Scenario: The pack library lives next to ES-DE's media folder unless set
    Given ES-DE keeps its media in "ES-DE/downloaded_media"
    Then the pack library should be "ES-DE/emumovies-artwork"
    When the pack library is set to "~/Packs"
    Then the pack library should be "~/Packs" expanded

  Scenario: Games get their missing images from the library, linked to save space
    Given the library holds "psx/covers/Spyro the Dragon (USA).png" and "psx/3dboxes/Spyro the Dragon (USA).png"
    And "psx/Spyro.chd" already has an ES-DE "3dboxes" image
    When images are filled from the library for "psx/Spyro.chd" named "Spyro the Dragon (USA)"
    Then the library should have filled "covers"
    And the ES-DE "covers" image should be linked to the library's

  Scenario: Images are copied when they can't be linked
    Given the library holds "psx/covers/Spyro the Dragon (USA).png" and "psx/3dboxes/Spyro the Dragon (USA).png"
    And files can't be linked
    When images are filled from the library for "psx/Spyro.chd" named "Spyro the Dragon (USA)"
    Then the library should have filled "covers, 3dboxes"
    And the ES-DE "covers" image should be a copy of the library's

  Scenario: Systems the library has nothing for get nothing
    Given the library holds "psx/covers/Spyro the Dragon (USA).png" and "psx/3dboxes/Spyro the Dragon (USA).png"
    When images are filled from the library for "snes/Chrono.sfc" named "Chrono Trigger (USA)"
    Then the library should have filled nothing

  Scenario: Several games of one system share the library's folder listing
    Given the library holds "psx/covers/Spyro the Dragon (USA).png" and "psx/covers/Final Fantasy VII (USA) (Disc 1).png"
    When images are filled from the library for "psx/Spyro.chd" named "Spyro the Dragon (USA)"
    And images are filled from the same library for "psx/FF7.m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then the library should have filled "covers"
