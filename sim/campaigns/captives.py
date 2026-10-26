"""Captives of war join the winner's bonded people (Complaint 648). The hooks are called from the campaign phase when a
battle is decided and when a tile is taken; the rules are the agents' (`captives_from_losses`, `captives_from_conquest`)."""
from sim.agents.api import captives_from_conquest, captives_from_losses
from sim.demography.api import AddCaptives
from sim.geography.api import settlement
from sim.hazards.api import RecordWorldEvent


class Captives:
	"""Reads: tiles_owned_by, has_state, country_world. Sends AddCaptives, RecordWorldEvent."""

	def _add_captives(self, winner: str, loser: str, people: float, tile: str, cause: str) -> float:
		"""The winner's bonded stratum takes `people` of the loser's; the log keeps what was taken."""
		taken = self.needs.send(AddCaptives(winner, people)) if people > 0.0 else 0.0
		if taken > 0.0:
			self.needs.send(RecordWorldEvent("captives", actors=(winner, loser), tiles=(tile,), cause=cause,
			                                 facts={"people": taken}))
		return taken

	def take_captives_from_battle(self, winner: str, loser: str, loser_lost: float, tile: str) -> float:
		return self._add_captives(winner, loser, captives_from_losses(loser_lost), tile, "battle")

	def take_captives_from_conquest(self, winner: str, loser: str, tile: str) -> float:
		owned = self.needs.tiles_owned_by[loser]
		if tile not in owned or not self.needs.has_state[loser]:
			return 0.0
		people = float(self.needs.country_world[loser].population_total()) * settlement.population_share(owned, tile)
		return self._add_captives(winner, loser, captives_from_conquest(people), tile, "conquest")
