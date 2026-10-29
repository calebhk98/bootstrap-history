"""The state the scenario module owns: the clock and the modes the game was set up with."""
from dataclasses import dataclass, field
from typing import Set


@dataclass
class ScenarioWorld:
	year: int = 100
	said_condition: Set[str] = field(default_factory=set)   # hazard-condition messages already printed once
	fog: bool = False                                        # played under fog of war
	fuzzy_estimates: bool = False                            # needs of unfinished work shown as blurred estimates
	fuzzy_salt: int = 0                                      # the blur's salt, drawn the first time the option is turned on
