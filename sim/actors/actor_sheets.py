"""What a mod may read about one actor: plain data, never the actor or the registry, mixed into `Actors`."""
from typing import Any, Dict, Optional

from sim.assembly.api import Part


def sheet_of(actor: Any) -> Optional[Dict[str, Any]]:
	"""The actor's id, kind, purse, headcount, prominence and cause note; None for no actor."""
	if actor is None:
		return None
	return {"actor_id": actor.actor_id, "kind": actor.record.kind, "money": actor.money, "headcount": float(sum(actor.workforce.values())),
	        "prominence": actor.stance.prominence(), "cause": actor.record.cause}


class ActorSheets(Part):
	"""Needs: none."""

	def actor_exists(self, actor_id: str) -> bool:
		return self.parts.cast.cast().get(actor_id) is not None

	def actor_sheet(self, actor_id: str) -> Optional[Dict[str, Any]]:
		return sheet_of(self.parts.cast.cast().get(actor_id))
