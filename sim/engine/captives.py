"""Captives of war join the winner's bonded people (Complaint 648). The hook is called from campaign_year.py when a
battle is decided and when a tile is taken; the rules are the agents' (`captives_from_losses`, `captives_from_conquest`,
`add_captives`)."""
from sim.agents import api as agents_api
from sim.geography.api import settlement

from . import world_events


class CaptivesMixin:

    def _add_captives(self, winner: str, loser: str, people: float, tile: str, cause: str) -> float:
        """The winner's bonded stratum takes `people` of the loser's; the log keeps what was taken."""
        taken = agents_api.add_captives(self.actors, winner, people) if people > 0.0 else 0.0
        if taken > 0.0:
            world_events.record(self, "captives", actors=[winner, loser], tiles=[tile], cause=cause, people=taken)
        return taken

    def take_captives_from_battle(self, winner: str, loser: str, loser_lost: float, tile: str) -> float:
        return self._add_captives(winner, loser, agents_api.captives_from_losses(loser_lost), tile, "battle")

    def take_captives_from_conquest(self, winner: str, loser: str, tile: str) -> float:
        owned = self.tiles_owned_by(loser)
        if tile not in owned or not self.owner_has_state(loser):
            return 0.0
        people = float(self.owner_world(loser).population_total()) * settlement.population_share(owned, tile)
        return self._add_captives(winner, loser, agents_api.captives_from_conquest(people), tile, "conquest")
