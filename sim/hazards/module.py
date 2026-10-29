"""The hazards module: dated shocks and world hazards, and what counters them.

A civilisation's file dates its catastrophes (a plague, a sack, a war, a debasement); every seat meets each with its own
works, and the world is hit once at the mildest figure any seat leaves. Beside them fall the yearly chances that need no date
(a patron's death, a fire, banditry) and the base-rate shocks every country draws for. What a seat has built takes a share off
each harm, and the module is the one place those figures come from: the shocks apply them and the screens print them. It owns
the world event log and the world's output factor, and tells other owners what a hazard does to them by commands."""
from sim.assembly.api import Module

from .advice import Advice
from .causes import Causes
from .events import Events
from .knowledge_risk import KnowledgeRisk
from .random_events import RandomEvents
from .relief import Relief
from .sack import Sack
from .shocks import Shocks
from .world import WorldHazards


class Hazards(Relief, Advice, Causes, KnowledgeRisk, Shocks, RandomEvents, Sack, WorldHazards, Events, Module):

	def setup(self) -> None:
		self._counters_cache = None      # (the mechanics rows it was built from, the counters)
		self._goal_closure = None        # what the goal needs, kept the first time a sack asks
		self.disaster_this_year = None
