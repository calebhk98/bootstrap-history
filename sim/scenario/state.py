"""The state the scenario module owns: the clock and the modes the game was set up with."""
from dataclasses import dataclass, field


@dataclass
class ScenarioWorld:
	year: int = 100
	fog: bool = False                                        # played under fog of war
	fuzzy_estimates: bool = False                            # needs of unfinished work shown as blurred estimates
	fuzzy_salt: int = 0                                      # the blur's salt, drawn the first time the option is turned on
