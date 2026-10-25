Feature: Counting the games in a ROM library

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
      | Downloads/Tetris (World).gb                                  |
      | Downloads/Mystery Disc.iso                                   |
      | Downloads/Old Game.m3u/Old Game.m3u                          |
      | Downloads/playlist.m3u                                       |
    And "dreamcast/Shenmue (USA).cue" points at "Shenmue (USA) (Track 1).bin"
    When the library is scanned
    Then the games by system should be
      | system    | games |
      | snes      | 2     |
      | psx       | 2     |
      | dreamcast | 1     |
      | gb        | 1     |
      | ps5       | 1     |
    And the undetected files should be "Old Game.m3u, playlist.m3u"

  Scenario: Only the chosen systems are scanned
    Given a ROM library containing
      | path                                                         |
      | snes/Super Mario World (USA).sfc                             |
      | psx/Final Fantasy VII (USA).m3u/Final Fantasy VII (USA).m3u  |
      | psx/Crash Bandicoot (USA).chd                                |
      | Downloads/Tetris (World).gb                                  |
      | Downloads/playlist.m3u                                       |
      | Downloads/Old Game.m3u/Old Game.m3u                          |
    When the library is scanned for "psx, gb"
    Then the games by system should be
      | system | games |
      | psx    | 2     |
      | gb     | 1     |
    And there should be no undetected files

  Scenario: The system folders in a library are listed for choosing
    Given a ROM library containing
      | path                             |
      | snes/Super Mario World (USA).sfc |
      | psx/Crash Bandicoot (USA).chd    |
      | Downloads/Tetris (World).gb      |
      | .multifile/psx/Game/Game.cue     |
      | gb                               |
    Then the system folders should be "psx, snes"
