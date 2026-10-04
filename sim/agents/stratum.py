"""`Stratum`: one body of people of one country (slaves, the poor, artisans, the propertied ...).

A stratum is a headcount with a purse, a literacy share and unmet needs, never a set of individuals.
It has no research tree and copies nothing. Its yearly turn (`stratum_year`) earns, buys needs in
tiers, grows, schools and decides who moves; the registry-level settlement (`settle_strata`) carries
out what crosses to another stratum (people with their savings, a keeper's allowance).
"""
from typing import Any, List

from .base import RecordedActor
from .registry import register_actor_kind
from . import stratum_year

STRATUM_ID_PREFIX = "stratum:"


def stratum_id(country_key: str, name: str) -> str:
	return "%s%s:%s" % (STRATUM_ID_PREFIX, country_key, name)


class Stratum(RecordedActor):
	kind = "stratum"

	def country_key(self) -> str:
		"""The country part of the id, which is how this stratum's neighbours are named."""
		name_part = ":" + self.record.stratum
		return self.actor_id[len(STRATUM_ID_PREFIX):-len(name_part)]

	def neighbour_id(self, name: str) -> str:
		return stratum_id(self.country_key(), name)

	def is_bonded(self) -> bool:
		return bool(self.record.plan.get("bonded"))

	def imitation_candidates(self, world: Any) -> List[str]:
		return []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def learn(self, chain: List[str], world: Any) -> None:
		"""A body of people holds no research tree."""

	def advance(self, world: Any) -> None:
		stratum_year.run_year(self, world)


register_actor_kind("stratum", Stratum)
