"""
Step implementations for ROM detection tests
Uses pytest-bdd for behavior-driven testing
"""

from pathlib import Path
import pytest
from pytest_bdd import given, scenario, then, when, parsers

from modules.detection import detect_system
from config import SYSTEM_MAP, SYSTEM_PRIORITY


# Context fixture
@pytest.fixture
def rom_context():
    return {}


# Scenario decorators for parametrized tests
@scenario("../features/detection.feature", "Clear extensions are detected correctly")
def test_clear_extension_nes(rom_context):
    pass


@scenario("../features/detection.feature", "SNES ROM with clear extension detected")
def test_clear_extension_snes(rom_context):
    pass


@scenario("../features/detection.feature", "GBA ROM with clear extension detected")
def test_clear_extension_gba(rom_context):
    pass


@scenario(
    "../features/detection.feature", "PS2 ROM with folder hint and ambiguous extension"
)
def test_ambiguous_ps2(rom_context):
    pass


@scenario(
    "../features/detection.feature", "PSX ROM with folder hint and ambiguous extension"
)
def test_ambiguous_psx(rom_context):
    pass


@scenario(
    "../features/detection.feature", "PS3 ROM with folder hint and ambiguous extension"
)
def test_ambiguous_ps3(rom_context):
    pass


@scenario(
    "../features/detection.feature", "Sega CD ROM with folder hint and ISO extension"
)
def test_ambiguous_segacd(rom_context):
    pass


@scenario(
    "../features/detection.feature", "Saturn ROM with folder hint and CHD extension"
)
def test_folder_hint_saturn(rom_context):
    pass


@scenario(
    "../features/detection.feature", "GameCube ROM with folder hint and CHD extension"
)
def test_folder_hint_gc(rom_context):
    pass


@scenario(
    "../features/detection.feature", "Arcade ROM with folder hint and CHD extension"
)
def test_folder_hint_arcade(rom_context):
    pass


@scenario("../features/detection.feature", "PSX ROM with folder hint and CUE extension")
def test_cue_psx(rom_context):
    pass


@scenario(
    "../features/detection.feature", "Dreamcast ROM with folder hint and CUE extension"
)
def test_cue_dreamcast(rom_context):
    pass


@scenario("../features/detection.feature", "Switch ROM with XCI extension")
def test_modern_switch_xci(rom_context):
    pass


@scenario("../features/detection.feature", "Switch ROM with NSP extension")
def test_modern_switch_nsp(rom_context):
    pass


@scenario("../features/detection.feature", "FBNeo arcade ROM in arcade folder")
def test_arcade_fbneo(rom_context):
    pass


@scenario(
    "../features/detection.feature", "MAME ROM with arcade folder hint uses priority"
)
def test_arcade_priority(rom_context):
    pass


@scenario("../features/detection.feature", "System priority configuration is complete")
def test_priority_configuration(rom_context):
    pass


@scenario("../features/detection.feature", "System map has complete extension coverage")
def test_system_map_coverage(rom_context):
    pass


# Given steps - parametrized with parsers to extract path from feature file
@given(parsers.parse('a ROM with path "{path}"'))
def rom_with_path(rom_context, path):
    """Store the ROM path in context"""
    rom_context["rom_path"] = Path(path)


# When steps
@when("the system detection runs")
def system_detection_runs(rom_context):
    """Run system detection on the stored ROM path"""
    rom_path = rom_context.get("rom_path")
    if rom_path is None:
        raise ValueError("ROM path not set in context")
    rom_context["detected_system"] = detect_system(rom_path)


@when("checking system priority configuration")
def check_system_priority(rom_context):
    """Store system priority in context"""
    rom_context["priority"] = SYSTEM_PRIORITY
    rom_context["priority_valid"] = True


@when("checking system map coverage")
def check_system_map(rom_context):
    """Analyze system map coverage"""
    rom_context["system_map"] = SYSTEM_MAP
    rom_context["extension_count"] = len(SYSTEM_MAP)

    # Get unique systems
    all_systems = set()
    for extensions in SYSTEM_MAP.values():
        if isinstance(extensions, list):
            all_systems.update(extensions)
        else:
            all_systems.add(extensions)

    rom_context["unique_systems"] = all_systems


# Then steps - parametrized with parsers to extract expected value
@then(parsers.parse('the detected system should be "{expected}"'))
def detected_system_should_be(rom_context, expected):
    """Assert the detected system matches expected"""
    detected = rom_context.get("detected_system")
    assert detected == expected, f"Expected {expected}, but got {detected}"


@then("system priority should not be empty")
def priority_not_empty(rom_context):
    """Assert system priority has items"""
    priority = rom_context.get("priority", [])
    assert len(priority) > 0, "System priority is empty"


@then("all systems in priority should be strings")
def priority_all_strings(rom_context):
    """Assert all items in priority are strings"""
    priority = rom_context.get("priority", [])
    for system in priority:
        assert isinstance(system, str), f"System priority item is not string: {system}"


@then("system map should contain extensions")
def system_map_has_extensions(rom_context):
    """Assert system map is not empty"""
    system_map = rom_context.get("system_map", {})
    assert len(system_map) > 0, "System map is empty"


@then("all systems should be mapped to valid systems")
def all_systems_valid(rom_context):
    """Assert all systems in map are valid strings"""
    system_map = rom_context.get("system_map", {})
    for extension, systems in system_map.items():
        assert isinstance(extension, str), f"Extension key is not string: {extension}"
        if isinstance(systems, list):
            for system in systems:
                assert isinstance(system, str), f"System is not string: {system}"
        else:
            assert isinstance(systems, str), f"System is not string: {systems}"


@then("system map should have at least 100 extensions")
def system_map_coverage_check(rom_context):
    """Assert system map has good coverage"""
    extension_count = rom_context.get("extension_count", 0)
    assert (
        extension_count >= 100
    ), f"System map has only {extension_count} extensions, expected at least 100"
