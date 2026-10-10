"""`Foundation`: a body of people kept by endowments, tithes and patrons, and paid a stipend (a church, an academy).

It collects from three sources, each a measured quantity of the world: the rent of the land it holds
(hectares times the land market's rent), a tithe on what the society sells of the goods that serve one
need, and the patronage that pays for learning while few can read. It pays its people a stipend at the
going pay of their trade out of what it holds. A technique that takes the goods off the tithed market, or
that spreads schooling and so cheapens learning, cuts what it collects, and when that falls below what its
people had come to expect they are a group (`foundation_sectors`). Nothing here names a faith, a good or a
civilisation: the rates and the need are data on the cast entry that founds it.
"""
from typing import Any, Dict, List

from . import ledger
from .base import RecordedActor
from .edges import EDGE_ECONOMY
from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .registry import register_actor_kind
from .sector import Sector

ENDOWMENT = "endowment"
TITHES = "tithes"
PATRONAGE = "patronage"


def mean_literacy(world: Any) -> float:
	"""The members-weighted literacy of the country's bodies of people (0 for none)."""
	strata = world.country_strata()
	people = sum(stratum.record.members for stratum in strata)
	return sum(stratum.record.literacy * stratum.record.members for stratum in strata) / people if people > 0.0 else 0.0


class Foundation(RecordedActor):
	"""Collects, pays stipends, and keeps the sector its people form when the collections fall."""
	kind = "foundation"
	# the kind of sector its people form
	group_kind = "dependants"

	def imitation_candidates(self, world: Any) -> List[str]:
		return []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def learn(self, chain: List[str], world: Any) -> None:
		"""A foundation holds no research tree."""

	def stipends_due(self, world: Any) -> float:
		"""What its people are owed this year at the going pay of their trade."""
		record = self.record
		return record.members * world.pay_per_person_year(record.stipend_trade) if record.stipend_trade else 0.0

	def collections(self, world: Any) -> Dict[str, float]:
		"""This year's income by source: endowment rent, tithe, patronage."""
		record = self.record
		lines: Dict[str, float] = {}
		if record.endowment_hectares > 0.0:
			lines[ENDOWMENT] = record.endowment_hectares * world.land_rent_per_hectare()
		if record.tithe_rate > 0.0 and record.tithe_need:
			lines[TITHES] = record.tithe_rate * world.tithable_sales_value(record.tithe_need)
		if record.patronage_rate > 0.0:
			# patrons pay for what few can do: the share of the stipends they cover falls as literacy spreads
			# (TEMPORARY HEURISTIC, CLAUDE.md 4.4, until patrons are actors with purses of their own)
			lines[PATRONAGE] = record.patronage_rate * self.stipends_due(world) * (1.0 - mean_literacy(world))
		return lines

	def advance(self, world: Any) -> None:
		record = self.record
		lines = self.collections(world)
		record.revenue_by_form = lines
		income = sum(lines.values())
		if income > 0.0:
			ledger.transfer(world.edge(EDGE_ECONOMY), self, income, "collections")
		due = self.stipends_due(world)
		paid = min(due, max(0.0, self.money))
		if paid > 0.0:
			ledger.transfer(self, world.edge(EDGE_ECONOMY), paid, "stipends")
		record.need = {"stipends": due}
		record.unfunded = {"stipends": due - paid}


class Church(Foundation):
	"""A church: clergy kept by tithes and the rent of its endowments."""
	kind = "church"
	group_kind = "clergy"


class Academy(Foundation):
	"""An academy: scholars kept by patrons and endowments."""
	kind = "academy"
	group_kind = "scholars"


register_actor_kind("church", Church)
register_actor_kind("academy", Academy)


def remember_collections(foundations: List[Any]) -> None:
	"""Each year what a foundation's people expect from each source moves toward what it yielded (at the rate a
	body of people comes to expect its welfare); a source that yielded nothing yet is expected to yield nothing."""
	for foundation in foundations:
		record = foundation.record
		for line, amount in record.revenue_by_form.items():
			reference = record.income_reference.get(line, 0.0)
			record.income_reference[line] = (
				amount if reference <= 0.0 else reference + STRATUM_WELFARE_MEMORY_RATE * (amount - reference))


def foundation_sectors(foundations: List[Any]) -> List[Sector]:
	"""One sector for each foundation whose collections have fallen below what its people expected: the
	fall, source by source (a source doing better does not set off another's loss), and the people it kept;
	the cause names the sources that fell and by how much."""
	sectors = []
	for foundation in foundations:
		record = foundation.record
		if record.exited_year is not None or record.members <= 0.0:
			continue
		expected = sum(record.income_reference.values())
		falls = {line: reference - record.revenue_by_form.get(line, 0.0)
				 for line, reference in sorted(record.income_reference.items())
				 if reference > 0.0 and reference - record.revenue_by_form.get(line, 0.0) > 0.0}
		lost = sum(falls.values())
		if expected <= 0.0 or lost < STRATUM_GRIEVANCE_THRESHOLD * expected:
			continue
		words = ", ".join("%s %d%% below what they had come to expect" % (line, round(100.0 * fall / record.income_reference[line]))
						  for line, fall in falls.items())
		sectors.append(Sector(foundation.group_kind, foundation.actor_id, record.name or foundation.actor_id,
							  "what %s collects has fallen: %s" % (record.name or foundation.actor_id, words),
							  lost, expected, record.members, 1.0))
	return sectors
