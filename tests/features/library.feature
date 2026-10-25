Feature: Counting the games in a ROM library and finding new ones

  Scenario: Games are counted the way ES-DE lists them
    Given a ROM library containing
      | path                                                         |
      | snes/Super Mario World (USA).sfc                             |
      | snes/Chrono Trigger (USA).zip                                |
      | snes/systeminfo.txt                                          |
      | snes/.hidden.sfc                                             |
      | psx/Crash Bandicoot (USA).cue/Crash Bandicoot (USA).cue      |
      | psx/Crash Bandicoot (USA).cue/Crash Bandicoot (USA).bin      |
      | psx/Final Fantasy VII (USA).m3u/Final Fantasy VII (USA).m3u  |
      | psx/Final Fantasy VII (USA).m3u/FF7 (Disc 1).chd             |
      | psx/.backup/Old Game.chd                                     |
      | dreamcast/Shenmue (USA).cue                                  |
      | dreamcast/Shenmue (USA) (Track 1).bin                        |
      | .multifile/psx/Spyro (USA)/Spyro (USA).cue                   |
      | Downloads/Tetris (World).gb                                  |
      | Mystery Disc.iso                                             |
    And "dreamcast/Shenmue (USA).cue" points at "Shenmue (USA) (Track 1).bin"
    When the library is scanned
    Then the games by system should be
      | system    | games |
      | snes      | 2     |
      | psx       | 2     |
      | dreamcast | 1     |

  Scenario: Only the chosen systems are scanned
    Given a ROM library containing
      | path                                                         |
      | snes/Super Mario World (USA).sfc                             |
      | psx/Final Fantasy VII (USA).m3u/Final Fantasy VII (USA).m3u  |
      | psx/Crash Bandicoot (USA).chd                                |
      | gb/Tetris (World).gb                                         |
    When the library is scanned for "psx, gb"
    Then the games by system should be
      | system | games |
      | psx    | 2     |
      | gb     | 1     |

  Scenario: The system folders in a library are listed for choosing
    Given a ROM library containing
      | path                             |
      | snes/Super Mario World (USA).sfc |
      | psx/Crash Bandicoot (USA).chd    |
      | Downloads/Tetris (World).gb      |
      | .multifile/psx/Game/Game.cue     |
      | gb                               |
    Then the system folders should be "psx, snes"

  Scenario: Games dropped into the ROM folder are found until they're organised
    Given a ROM library containing
      | path                                                 |
      | snes/Super Mario World (USA).sfc                     |
      | Chrono Trigger (USA).sfc                             |
      | New Stuff/Tetris (World).gb                          |
      | New Stuff/readme.txt                                 |
      | New Stuff/.DS_Store                                  |
      | psx/Crash Bandicoot (USA).cue                        |
      | psx/Crash Bandicoot (USA).bin                        |
      | psx/Final Fantasy VII (USA) (Disc 1).chd             |
      | psx/Spyro (USA).chd                                  |
      | psx/More/Tomba (USA) (Disc 2).chd                    |
      | psx/Medievil (USA).m3u                               |
      | psx/Legend of Dragoon (USA).m3u/LoD (Disc 1).chd     |
      | .multifile/psx/Medievil (USA)/Medievil (USA).cue     |
      | pcenginecd/Ys Book I & II (USA).cue                  |
      | pcenginecd/Ys Book I & II (USA).bin                  |
    And "psx/Crash Bandicoot (USA).cue" points at "Crash Bandicoot (USA).bin"
    And "pcenginecd/Ys Book I & II (USA).cue" points at "Ys Book I & II (USA).bin"
    And the app has organised "snes/Super Mario World (USA).sfc, psx/Spyro (USA).chd, psx/Final Fantasy VII (USA) (Disc 1).chd, pcenginecd/Ys Book I & II (USA).cue"
    When new games are looked for
    Then the games waiting to be organised should be
      | game                                     | tracks                         |
      | Chrono Trigger (USA).sfc                 |                                |
      | New Stuff/Tetris (World).gb              |                                |
      | psx/Crash Bandicoot (USA).cue            | psx/Crash Bandicoot (USA).bin  |
      | psx/Final Fantasy VII (USA) (Disc 1).chd |                                |
      | psx/More/Tomba (USA) (Disc 2).chd        |                                |

  Scenario: A game dropped into its system folder is new until it's organised, and again if it changes
    Given a ROM library containing
      | path                             |
      | snes/Chrono Trigger (USA).sfc    |
      | snes/Super Mario World (USA).sfc |
    And the app has organised "snes/Super Mario World (USA).sfc"
    When new games are looked for
    Then the games waiting to be organised should be "snes/Chrono Trigger (USA).sfc"
    When the app has organised "snes/Chrono Trigger (USA).sfc"
    And "snes/Super Mario World (USA).sfc" is replaced
    And new games are looked for
    Then the games waiting to be organised should be "snes/Super Mario World (USA).sfc"

  Scenario: Without a cache every game in the ROM folder is new
    Given a ROM library containing
      | path                          |
      | snes/Chrono Trigger (USA).sfc |
    When new games are looked for without a cache
    Then the games waiting to be organised should be "snes/Chrono Trigger (USA).sfc"

  Scenario: In the ES-DE layout every system's multi-file games are organised, except arcade ones
    Given the ES-DE folder layout is chosen
    And a ROM library containing
      | path                                     |
      | pcenginecd/Ys Book I & II (USA).cue      |
      | pcenginecd/Ys Book I & II (USA).bin      |
      | mame/Street Fighter (Disc 1).zip         |
    And "pcenginecd/Ys Book I & II (USA).cue" points at "Ys Book I & II (USA).bin"
    And the app has organised "pcenginecd/Ys Book I & II (USA).cue, mame/Street Fighter (Disc 1).zip"
    When new games are looked for
    Then the games waiting to be organised should be
      | game                                | tracks                              |
      | pcenginecd/Ys Book I & II (USA).cue | pcenginecd/Ys Book I & II (USA).bin |
