"""The state the ventures module owns: one seat's businesses and the plants they run."""
from dataclasses import dataclass, field
from typing import List

from sim.agents.api import Business


@dataclass
class VenturesSeat:
	# the seat's businesses and their plants, the first being the seat's own: what is running, switched off, how big and since when
	businesses: List[Business] = field(default_factory=lambda: [Business(business_id="founder")])

	@property
	def business(self) -> Business:
		"""The seat's own business, which holds the plants it runs."""
		return self.businesses[0]
