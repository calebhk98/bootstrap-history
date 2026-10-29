"""Commands to the owner of the household's people that the year's money phase sends: the living cost, and the standing policies on
buying and freeing people."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class ChargeLivingCost(Command):
	"""The year's living cost is billed to the acting seat: `living_cost` less the `dependants_beyond_means` its income cannot carry
	and less the wages already paid in advance (which are then used up). Answers the amount to pay."""
	living_cost: float
	dependants_beyond_means: float


@dataclass(frozen=True)
class AutoBuyPeople(Command):
	"""The acting seat's standing policy to buy people, when it is switched on, the purse is deep enough, the artisans few and a
	running mechanic hosts bought people: buys them and records the purchase."""


@dataclass(frozen=True)
class AutoManumit(Command):
	"""The acting seat's standing policy to free people, when it is switched on and slaves are held: draws the game's dice once and
	on a hit frees a share of them and records it."""


@dataclass(frozen=True)
class FadeMarketPressure(Command):
	"""A year passes on the people market: the pressure the acting seat's buying put on it fades."""


@dataclass(frozen=True)
class NoteBuyRefusal(Command):
	"""Why the acting seat's last attempt to buy people was refused, for the screen that asked (None clears it). Never saved."""
	refusal: Optional[str]
