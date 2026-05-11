#!/usr/bin/env python3
"""
Test script to validate enhanced detection and configuration
"""

from pathlib import Path
from modules.detection import detect_system
from config import SYSTEM_MAP, SYSTEM_PRIORITY


def test_detection():
    """Test system detection with various scenarios"""

    print("=" * 60)
    print("Testing Enhanced System Detection")
    print("=" * 60)

    # Test cases: (path, expected_system)
    test_cases = [
        # Clear extensions (no ambiguity)
        (Path("/roms/nes/super_mario.nes"), "nes"),
        (Path("/roms/snes/chrono.smc"), "snes"),
        (Path("/roms/gba/fire_emblem.gba"), "gba"),
        # Ambiguous extensions - should use folder hints and priority
        (Path("/roms/ps2/final_fantasy_vii.iso"), "ps2"),
        (Path("/roms/psx/final_fantasy_vii.iso"), "psx"),
        (Path("/roms/ps3/final_fantasy_xv.iso"), "ps3"),
        (Path("/roms/segacd/sonic_cd.iso"), "segacd"),
        # CHD files (ambiguous - saturn, gc, arcade, mame)
        (Path("/roms/saturn/sonic_adventure.chd"), "saturn"),  # Has saturn hint
        (Path("/roms/gamecube/zelda_windwaker.chd"), "gc"),  # Has gc hint
        (Path("/roms/arcade/caveman_ninja.chd"), "fbneo"),  # Folder hint for arcade
        # CUE files (ps1, dreamcast, segacd)
        (Path("/roms/psx/metal_gear_solid.cue"), "psx"),  # Has psx hint
        (Path("/roms/dreamcast/shenmue.cue"), "dreamcast"),  # Has dreamcast hint
        # Modern systems
        (Path("/roms/switch/zelda_totk.xci"), "switch"),
        (Path("/roms/switch/mario_kart.nsp"), "switch"),
        # Arcade detection via folder
        (Path("/arcade/fbneo/pacman.zip"), "fbneo"),
        (Path("/arcade/mame/mortal_kombat.7z"), "fbneo"),  # Priority over mame
    ]

    print("\nTest Results:")
    print("-" * 60)

    passed = 0
    failed = 0

    for test_path, expected in test_cases:
        result = detect_system(test_path)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}: {str(test_path)}")
        print(f"       Expected: {expected}, Got: {result}")

    print("-" * 60)
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")

    return failed == 0


def test_system_priority():
    """Test SYSTEM_PRIORITY configuration"""

    print("\n" + "=" * 60)
    print("System Priority Configuration")
    print("=" * 60)

    print(f"\nSYSTEM_PRIORITY (for disambiguation when extensions overlap):")
    for i, system in enumerate(SYSTEM_PRIORITY, 1):
        print(f"  {i}. {system}")

    return True


def test_system_map_coverage():
    """Test SYSTEM_MAP coverage"""

    print("\n" + "=" * 60)
    print("SYSTEM_MAP Coverage")
    print("=" * 60)

    system_count = len(set(SYSTEM_MAP.values()))
    extension_count = len(SYSTEM_MAP)

    print(f"\nTotal extensions: {extension_count}")
    print(f"Total unique systems: {system_count}")

    # Group by system
    systems = {}
    for ext, sys in SYSTEM_MAP.items():
        if sys not in systems:
            systems[sys] = []
        systems[sys].append(ext)

    print("\nSystems by extension count:")
    for system in sorted(systems.keys()):
        ext_list = sorted(systems[system])
        print(f"  {system}: {', '.join(ext_list)}")

    return True


if __name__ == "__main__":
    success = True

    success &= test_detection()
    success &= test_system_priority()
    success &= test_system_map_coverage()

    print("\n" + "=" * 60)
    if success:
        print("✓ All tests completed successfully!")
    else:
        print("✗ Some tests failed. Please review above.")
    print("=" * 60)
