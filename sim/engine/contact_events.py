"""Contact events the engine reports to the actors: a migration raises the receivers' awareness of what the people met know
(the actors module records it; the rules are sim/actors/rules.py)."""
from typing import Any, Iterable, Tuple

from sim.actors.api import RecordMigrationContact


def after_migration(sim: Any, pairs: Iterable[Tuple[str, str, float]]) -> None:
	"""Actors where migrants arrive become aware of what the people of the place the migrants left know."""
	sim.send(RecordMigrationContact(tuple((origin, destination, moved) for origin, destination, moved in pairs)))
