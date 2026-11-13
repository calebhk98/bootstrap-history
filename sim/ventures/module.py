"""The ventures module: the seat's businesses and the plants they run, what a seat's concerns tie up and cost, opening one by
hand, the founder's sales and the roll-out of public works.

The businesses are its seat state, written only by its commands (a deal's plants pass by `ReleasePlant` and `AdoptPlant`). The views
over what is operating and shut hand out copies of the record's sets, and are uncached."""
from sim.assembly.api import Module

from .coverage import Coverage
from .crew import Crew
from .opening import Opening
from .plants import Plants
from .quotes import Quotes
from .sales import Sales


class Ventures(Module):

	PARTS = {
		"plants": Plants,
		"crew": Crew,
		"quotes": Quotes,
		"opening": Opening,
		"sales": Sales,
		"coverage": Coverage,
	}
