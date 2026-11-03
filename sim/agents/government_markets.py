"""What a state will sell abroad, and to whom: its own policy answers the export decision, and it can close its markets to a party."""
from typing import Any

from . import policy


class Markets:
	"""A state's sales abroad and closed markets, on the government that owns the record."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def exports_allowed(self, materials: Any) -> list:
		"""The materials, sorted, this state will sell abroad."""
		return policy.exports_allowed(self.government, materials)

	def close_markets_to(self, party_id: str, until_year: int) -> None:
		"""Refuse every sale to a party (caught smuggling, say) until the year; a longer closure stands."""
		closed = self.government.record.closed_markets
		closed[party_id] = max(int(until_year), closed.get(party_id, 0))

	def markets_closed_until(self, party_id: str, year: int) -> int:
		"""The first year the party may buy here again, or 0 when its markets are open to it in `year`."""
		until = self.government.record.closed_markets.get(party_id, 0)
		return until if until > year else 0
