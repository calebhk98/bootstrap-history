"""Regression coverage for combined tech-tree realism review, part 04."""
from .harness import *  # noqa: F401,F403


check("medieval clockwork is split from pendulum timekeeping",
      NODES["clock_pendulum"]["pre"][0] == "clock_mechanical_escapement"
      and "pendulum" not in NODES["clock_mechanical_escapement"]["name"].lower(),
      NODES["clock_pendulum"]["pre"])
check("the inherited watermill node no longer claims general line shafting",
      "line shaft" not in NODES["water_power_scale"]["name"].lower()
      and "not included" in NODES["water_power_scale"]["note"],
      NODES["water_power_scale"]["note"])
