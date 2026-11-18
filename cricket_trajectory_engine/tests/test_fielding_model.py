"""
Unit tests for the Authentic Cricket Fielding Domain Model.
Validates the strict 11-player rule, realistic presets, and ICC format restriction rules.
"""

import pytest

from cricket_trajectory_engine.models.fielder import (
    FielderModel,
    FieldingSetupModel,
    FIELDING_PRESETS,
)


def test_presets_have_exactly_11_players():
    """Verify that all default fielding presets contain strictly 11 players."""
    presets = ["powerplay", "attacking", "middle_overs", "death_overs"]
    for preset_name in presets:
        setup = FieldingSetupModel.from_preset(preset_name)
        assert len(setup.fielders) == 11, f"Preset {preset_name} has {len(setup.fielders)} players, expected 11"
        names = [f.name for f in setup.fielders]
        assert any("Keeper" in n for n in names), f"Preset {preset_name} missing Wicket-Keeper"
        assert "Bowler" in names, f"Preset {preset_name} missing Bowler"


def test_t20_powerplay_validation():
    """Verify that T20 Powerplay allows at most 2 fielders outside the 30-yard circle."""
    # Standard powerplay preset has 2 fielders deep
    setup = FieldingSetupModel.from_preset("powerplay")
    setup.format_rules = "t20_powerplay"
    violations = setup.validate_rules()
    assert len(violations) == 0, f"Expected powerplay preset to be valid, got violations: {violations}"

    # Invalid: Add a 3rd deep fielder
    bad_fielders = list(setup.fielders)
    # Move Point (at 4, 21) out to deep cover (45, 45 -> dist ~63m from center)
    for i, f in enumerate(bad_fielders):
        if f.id == "point":
            bad_fielders[i] = FielderModel(id="point", name="Deep Point", role="fielder", x_m=45.0, y_m=45.0)
            break
    
    bad_setup = FieldingSetupModel(fielders=bad_fielders, format_rules="t20_powerplay")
    violations_bad = bad_setup.validate_rules()
    assert len(violations_bad) > 0
    assert any("powerplay violation" in v.lower() for v in violations_bad)


def test_law_28_4_leg_side_behind_square_limit():
    """Verify ICC Law 28.4: At most 2 fielders allowed behind square on the leg side."""
    setup = FieldingSetupModel.from_preset("powerplay")
    bad_fielders = list(setup.fielders)
    
    # In fielding model coordinate system, behind square leg means x_m < 0 and y_m < 0:
    bad_fielders[0] = FielderModel(id="f1", name="Leg Slip 1", role="fielder", x_m=-2.0, y_m=-5.0)
    bad_fielders[1] = FielderModel(id="f2", name="Leg Slip 2", role="fielder", x_m=-4.0, y_m=-8.0)
    bad_fielders[2] = FielderModel(id="f3", name="Fine Leg", role="fielder", x_m=-15.0, y_m=-20.0)

    illegal_setup = FieldingSetupModel(fielders=bad_fielders, format_rules="test")
    violations = illegal_setup.validate_rules()
    assert len(violations) > 0
    assert any("law 28.4" in v.lower() for v in violations)


def test_non_11_players_rejected():
    """Verify that setups with fewer or more than 11 players fail validation."""
    ten_fielders = [
        FielderModel(id=f"f_{i}", name=f"Fielder {i}", role="fielder", x_m=float(i), y_m=0.0)
        for i in range(10)
    ]
    setup = FieldingSetupModel(fielders=ten_fielders)
    violations = setup.validate_rules()
    assert len(violations) > 0
    assert any("must have exactly 11 players" in v.lower() for v in violations)
