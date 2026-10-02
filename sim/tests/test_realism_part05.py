"""Regression coverage for combined tech-tree realism review, part 05."""
from .harness import *  # noqa: F401,F403


check("human mechanisms and animal machines use distinct capability gates",
      NODES["cn_crane_treadwheel"]["pre"][0] == "cap_power_human"
      and "cap_power_muscle" in NODES["en_horse_gin"]["pre"]
      and "cap_power_muscle" in NODES["pwr_animal_treadmill"]["pre"],
      {i: NODES[i]["pre"] for i in
       ("cn_crane_treadwheel", "en_horse_gin", "pwr_animal_treadmill")})
