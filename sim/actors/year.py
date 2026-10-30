"""The actors' year: every government, player, firm, trader and body of people decides, pays and posts."""
from typing import Any

from sim.agents.api import true_up_keep
from sim.coin.api import ChargeActorsTheft, ChargeKeeping
from sim.finance.api import RefreshLenderOffers
from sim.production.api import AccrueExperience


class Year:
	"""Mixed into `Actors`."""

	needs: Any

	def advance_actors(self, command: Any) -> None:
		"""Give every actor its year. Coin moved between actors in different places pays carriage meanwhile."""
		with self.needs.transfer_listening():
			self.seed_opening_cast()  # type: ignore[attr-defined]
			self.state_treasury()  # type: ignore[attr-defined]
			self.needs.send(RefreshLenderOffers())
			world = self.actor_world()  # type: ignore[attr-defined]
			registry = self.cast()  # type: ignore[attr-defined]
			true_up_keep(registry, world)
			registry.advance(world)
			self.needs.send(AccrueExperience())
			self.needs.send(ChargeKeeping())
			self.needs.send(ChargeActorsTheft())
