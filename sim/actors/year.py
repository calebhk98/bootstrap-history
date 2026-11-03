"""The actors' year: every government, player, firm, trader and body of people decides, pays and posts."""
from typing import Any

from sim.agents.api import true_up_keep
from sim.assembly.api import Part
from sim.coin.api import ChargeActorsTheft, ChargeKeeping
from sim.finance.api import RefreshLenderOffers
from sim.production.api import AccrueExperience


class Year(Part):

	def advance_actors(self, command: Any) -> None:
		"""Give every actor its year. Coin moved between actors in different places pays carriage meanwhile."""
		with self.needs.transfer_listening():
			self.parts.cast.seed_opening_cast()
			self.parts.cast.state_treasury()
			self.needs.send(RefreshLenderOffers())
			world = self.parts.cast.actor_world()
			registry = self.parts.cast.cast()
			true_up_keep(registry, world)
			registry.advance(world)
			self.needs.send(AccrueExperience())
			self.needs.send(ChargeKeeping())
			self.needs.send(ChargeActorsTheft())
