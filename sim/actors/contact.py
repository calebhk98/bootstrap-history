"""What the actors become aware of when armies and people cross borders, and a trader's margin."""
from typing import Any, Dict, List, Optional

from sim.agents.api import CONQUEST_CONTACT_VOLUME, MIGRANT_CONTACT_VOLUME_PER_PERSON, awareness
from sim.refusal import Refusal

from . import rules


class Contact:
	"""Mixed into `Actors`."""

	needs: Any

	def record_conquest_contact(self, command: Any) -> None:
		"""The winner's actors become aware of what the overrun country's people know."""
		registry = self.cast()  # type: ignore[attr-defined]
		places_by_country: Dict[Optional[str], List[Any]] = {}
		receivers = []
		for actor_id in sorted(registry.actors):
			actor = registry.actors[actor_id]
			country = registry.country_of(actor)
			places_by_country.setdefault(country, []).append(actor.location())
			if country == command.conqueror:
				receivers.append(actor)
		places = rules.conquest_contacts(places_by_country, command.previous, command.tile)
		awareness.record_contacts(receivers, places, CONQUEST_CONTACT_VOLUME)

	def record_migration_contact(self, command: Any) -> None:
		"""Actors where migrants arrive become aware of what the people of the place the migrants left know."""
		arriving = rules.migrants_arriving(command.moves, MIGRANT_CONTACT_VOLUME_PER_PERSON)
		if not arriving:
			return
		registry = self.cast()  # type: ignore[attr-defined]
		for actor_id in sorted(registry.actors):
			actor = registry.actors[actor_id]
			for origin, volume in sorted(arriving.get(actor.location(), {}).items()):
				awareness.record_contact(actor, origin, volume)

	def note_trader_margin(self, command: Any) -> Optional[Refusal]:
		"""The trader's last margin follows what its cargo made against what it was booked at."""
		trader = self.cast().actors.get(command.trader)  # type: ignore[attr-defined]
		if trader is None:
			return Refusal("no_such_actor", "the cast holds no trader %s" % command.trader)
		trader.record.last_margin += command.amount
		return None
