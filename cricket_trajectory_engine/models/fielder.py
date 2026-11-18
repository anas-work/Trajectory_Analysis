"""
Fielding Domain Model & Formation Engine.
Enforces authentic 11-player constraint (1 keeper, 1 bowler, 9 fielders),
tactical presets (Attacking, Defensive, Powerplay, Middle-overs, Death-overs),
and competition format restriction checks (Test, ODI, T20).
"""

import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class FielderModel:
    id: str
    name: str
    role: str                       # "wicketkeeper", "bowler", "fielder"
    x_m: float
    y_m: float
    reaction_time_s: float = 0.35   # Sports motor latency
    max_sprint_speed_m_s: float = 7.0 # Elite fielder sprint (25.2 km/h)
    reach_radius_m: float = 1.8     # Diving/extension reach
    min_catch_height_m: float = 0.25 # Shoestring catch limit
    max_catch_height_m: float = 2.30 # Jumping reach limit

    def distance_from_striker(self) -> float:
        return math.hypot(self.x_m, self.y_m)

    def is_inside_circle(self, pitch_length_m: float = 20.12, circle_radius_m: float = 27.43) -> bool:
        center_x = pitch_length_m / 2.0
        return math.hypot(self.x_m - center_x, self.y_m) <= circle_radius_m

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


FIELDER_MOBILITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "static": {
        "name": "Static Mode (Stationary)",
        "max_sprint_speed_m_s": 0.0,
        "reaction_time_s": 0.35,
        "reach_radius_m": 1.8,
        "min_catch_height_m": 0.25,
        "max_catch_height_m": 2.30,
        "standing_reach_m": 2.25,
        "body_height_m": 1.80,
        "acceleration_m_s2": 0.0,
    },
    "club": {
        "name": "Club Mode (Recreational)",
        "max_sprint_speed_m_s": 5.0,
        "reaction_time_s": 0.45,
        "reach_radius_m": 1.5,
        "min_catch_height_m": 0.30,
        "max_catch_height_m": 2.15,
        "standing_reach_m": 2.15,
        "body_height_m": 1.75,
        "acceleration_m_s2": None,
    },
    "elite": {
        "name": "Elite Mode (International)",
        "max_sprint_speed_m_s": 7.0,
        "reaction_time_s": 0.35,
        "reach_radius_m": 1.8,
        "min_catch_height_m": 0.25,
        "max_catch_height_m": 2.30,
        "standing_reach_m": 2.30,
        "body_height_m": 1.82,
        "acceleration_m_s2": None,
    },
}


FIELDING_PRESETS: Dict[str, Dict[str, Any]] = {
    "powerplay": {
        "name": "T20 / ODI Powerplay Field (Ring Packed, 2 Deep)",
        "description": "Standard limited-overs powerplay: 9 players inside the 30-yard circle, exactly 2 deep boundary fielders.",
        "format": "t20_powerplay",
        "fielders": [
            {"id": "wk", "name": "Wicket-Keeper", "role": "wicketkeeper", "x": -3.8, "y": 0.2},
            {"id": "bowl", "name": "Bowler", "role": "bowler", "x": 20.12, "y": 0.0},
            {"id": "slip1", "name": "1st Slip", "role": "fielder", "x": -6.2, "y": 2.6},
            {"id": "point", "name": "Point", "role": "fielder", "x": 4.0, "y": 21.0},
            {"id": "cover", "name": "Cover", "role": "fielder", "x": 17.0, "y": 18.0},
            {"id": "mid_off", "name": "Mid-Off", "role": "fielder", "x": 26.0, "y": 7.0},
            {"id": "mid_on", "name": "Mid-On", "role": "fielder", "x": 26.0, "y": -7.0},
            {"id": "mid_wicket", "name": "Mid-Wicket", "role": "fielder", "x": 17.0, "y": -18.0},
            {"id": "sq_leg", "name": "Square Leg", "role": "fielder", "x": 3.0, "y": -20.0},
            {"id": "deep_mid_wicket", "name": "Deep Mid-Wicket", "role": "fielder", "x": 46.0, "y": -48.0},
            {"id": "third_man", "name": "Third Man", "role": "fielder", "x": -32.0, "y": 42.0},
        ]
    },
    "attacking": {
        "name": "Test Match Attacking (3 Slips, Gully, Short Leg)",
        "description": "Close catching cordon for pacers seeking outside and inside edges.",
        "format": "test",
        "fielders": [
            {"id": "wk", "name": "Wicket-Keeper", "role": "wicketkeeper", "x": -4.2, "y": 0.3},
            {"id": "bowl", "name": "Bowler", "role": "bowler", "x": 20.12, "y": 0.0},
            {"id": "slip1", "name": "1st Slip", "role": "fielder", "x": -6.5, "y": 2.5},
            {"id": "slip2", "name": "2nd Slip", "role": "fielder", "x": -7.2, "y": 4.5},
            {"id": "slip3", "name": "3rd Slip", "role": "fielder", "x": -7.8, "y": 6.8},
            {"id": "gully", "name": "Gully", "role": "fielder", "x": -3.5, "y": 12.0},
            {"id": "point", "name": "Point", "role": "fielder", "x": 3.5, "y": 18.0},
            {"id": "mid_off", "name": "Mid-Off", "role": "fielder", "x": 25.0, "y": 8.0},
            {"id": "mid_on", "name": "Mid-On", "role": "fielder", "x": 25.0, "y": -8.0},
            {"id": "mid_wicket", "name": "Mid-Wicket", "role": "fielder", "x": 16.0, "y": -16.0},
            {"id": "sq_leg", "name": "Square Leg", "role": "fielder", "x": 3.0, "y": -18.0},
        ]
    },
    "middle_overs": {
        "name": "Middle-Overs Consolidation (4 Deep)",
        "description": "Balanced field with 4 sweepers on the boundary protecting boundaries and 5 ring fielders stopping singles.",
        "format": "odi_middle",
        "fielders": [
            {"id": "wk", "name": "Wicket-Keeper", "role": "wicketkeeper", "x": -3.8, "y": 0.2},
            {"id": "bowl", "name": "Bowler", "role": "bowler", "x": 20.12, "y": 0.0},
            {"id": "point", "name": "Point", "role": "fielder", "x": 4.0, "y": 20.0},
            {"id": "cover", "name": "Cover", "role": "fielder", "x": 16.0, "y": 18.0},
            {"id": "mid_wicket", "name": "Mid-Wicket", "role": "fielder", "x": 16.0, "y": -18.0},
            {"id": "extra_cover", "name": "Extra Cover", "role": "fielder", "x": 24.0, "y": 12.0},
            {"id": "mid_on", "name": "Mid-On", "role": "fielder", "x": 24.0, "y": -8.0},
            {"id": "deep_cover", "name": "Deep Cover", "role": "fielder", "x": 45.0, "y": 45.0},
            {"id": "long_off", "name": "Long-Off", "role": "fielder", "x": 64.0, "y": 14.0},
            {"id": "long_on", "name": "Long-On", "role": "fielder", "x": 64.0, "y": -14.0},
            {"id": "deep_mid_wicket", "name": "Deep Mid-Wicket", "role": "fielder", "x": 45.0, "y": -46.0},
        ]
    },
    "death_overs": {
        "name": "Death-Overs Boundary Protection (5 Deep)",
        "description": "Maximum allowed boundary riders (5 deep) guarding straight and square boundaries against lofted shots.",
        "format": "t20_death",
        "fielders": [
            {"id": "wk", "name": "Wicket-Keeper", "role": "wicketkeeper", "x": -4.0, "y": 0.0},
            {"id": "bowl", "name": "Bowler", "role": "bowler", "x": 20.12, "y": 0.0},
            {"id": "point", "name": "Point", "role": "fielder", "x": 4.0, "y": 20.0},
            {"id": "cover", "name": "Cover", "role": "fielder", "x": 16.0, "y": 16.0},
            {"id": "mid_wicket", "name": "Mid-Wicket", "role": "fielder", "x": 16.0, "y": -16.0},
            {"id": "deep_point", "name": "Deep Point", "role": "fielder", "x": 12.0, "y": 62.0},
            {"id": "deep_cover", "name": "Deep Cover", "role": "fielder", "x": 42.0, "y": 48.0},
            {"id": "long_off", "name": "Long-Off", "role": "fielder", "x": 64.0, "y": 15.0},
            {"id": "long_on", "name": "Long-On", "role": "fielder", "x": 64.0, "y": -15.0},
            {"id": "deep_mid_wicket", "name": "Deep Mid-Wicket", "role": "fielder", "x": 42.0, "y": -48.0},
            {"id": "deep_sq_leg", "name": "Deep Square Leg", "role": "fielder", "x": 10.0, "y": -62.0},
        ]
    },
    "square_leg_study": {
        "name": "Square Leg & Deep Square Leg Focus (Trajectory Study)",
        "description": "Tactical study setup with calibrated Square Leg (+3.0m, -20.0m) and Deep Square Leg (+10.0m, -62.0m).",
        "format": "custom",
        "fielders": [
            {"id": "wk", "name": "Wicket-Keeper", "role": "wicketkeeper", "x": -3.8, "y": 0.2},
            {"id": "bowl", "name": "Bowler", "role": "bowler", "x": 20.12, "y": 0.0},
            {"id": "slip1", "name": "1st Slip", "role": "fielder", "x": -6.2, "y": 2.6},
            {"id": "point", "name": "Point", "role": "fielder", "x": 4.0, "y": 21.0},
            {"id": "cover", "name": "Cover", "role": "fielder", "x": 17.0, "y": 18.0},
            {"id": "mid_off", "name": "Mid-Off", "role": "fielder", "x": 26.0, "y": 7.0},
            {"id": "mid_on", "name": "Mid-On", "role": "fielder", "x": 26.0, "y": -7.0},
            {"id": "mid_wicket", "name": "Mid-Wicket", "role": "fielder", "x": 17.0, "y": -18.0},
            {"id": "sq_leg", "name": "Square Leg", "role": "fielder", "x": 3.0, "y": -20.0},
            {"id": "deep_sq_leg", "name": "Deep Square Leg", "role": "fielder", "x": 10.0, "y": -62.0},
            {"id": "third_man", "name": "Third Man", "role": "fielder", "x": -32.0, "y": 42.0},
        ]
    }
}


@dataclass
class FieldingSetupModel:
    fielders: List[FielderModel] = field(default_factory=list)
    format_rules: str = "t20"       # "test", "odi_p1", "odi_p2", "odi_p3", "t20", "custom"
    active_preset: str = "powerplay"

    @classmethod
    def from_preset(cls, preset_key: str = "powerplay") -> "FieldingSetupModel":
        preset = FIELDING_PRESETS.get(preset_key, FIELDING_PRESETS["powerplay"])
        f_list = [
            FielderModel(
                id=item["id"],
                name=item["name"],
                role=item["role"],
                x_m=float(item["x"]),
                y_m=float(item["y"]),
            )
            for item in preset["fielders"]
        ]
        return cls(fielders=f_list, format_rules="t20", active_preset=preset_key)

    def validate_rules(self, pitch_length_m: float = 20.12, circle_radius_m: float = 27.43) -> List[str]:
        """Validates fielding setup against official cricket rules & formats."""
        warnings = []
        if len(self.fielders) != 11:
            warnings.append(f"A cricket fielding side MUST have exactly 11 players (got {len(self.fielders)}).")

        n_outside = sum(1 for f in self.fielders if not f.is_inside_circle(pitch_length_m, circle_radius_m))

        if self.format_rules == "t20_powerplay" and n_outside > 2:
            warnings.append(f"T20 Powerplay violation: Maximum 2 fielders allowed outside the 30-yard circle (currently {n_outside}).")
        elif self.format_rules == "t20" and n_outside > 5:
            warnings.append(f"T20 Fielding restriction violation: Maximum 5 fielders allowed outside the 30-yard circle (currently {n_outside}).")
        elif self.format_rules == "odi_p1" and n_outside > 2:
            warnings.append(f"ODI Powerplay 1 violation: Maximum 2 fielders allowed outside the 30-yard circle (currently {n_outside}).")
        elif self.format_rules == "odi_p2" and n_outside > 4:
            warnings.append(f"ODI Powerplay 2 violation: Maximum 4 fielders allowed outside the 30-yard circle (currently {n_outside}).")
        elif self.format_rules == "odi_p3" and n_outside > 5:
            warnings.append(f"ODI Powerplay 3 violation: Maximum 5 fielders allowed outside the 30-yard circle (currently {n_outside}).")

        # Leg-side boundary restriction (Law 28.4: At most 2 fielders behind square on leg side):
        n_behind_square_leg = sum(1 for f in self.fielders if f.x_m < 0 and f.y_m < 0)
        if n_behind_square_leg > 2:
            warnings.append(f"Law 28.4 violation: At most 2 fielders permitted behind square on the leg side (currently {n_behind_square_leg}).")

        return warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_players": len(self.fielders),
            "format_rules": self.format_rules,
            "active_preset": self.active_preset,
            "fielders": [f.to_dict() for f in self.fielders],
            "rule_warnings": self.validate_rules(),
        }

