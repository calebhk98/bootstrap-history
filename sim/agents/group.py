"""`InterestGroup`: people who share a loss and act on the state about it.

A group exists while the income its members lost to one cause stays above what it takes to
organise. Its pull on the state grows with that loss as a share of the revenue of the territory
it lives in. The state answers by what it can do (`state_response`): make the loss good from its
purse, forbid the technique if it can afford to forgo the gains, and let the blame fall on the
founder either way. Nothing here names a trade, a commodity or a civilisation.
"""
import math
from typing import Any, Dict, List

from .base import RecordedActor
from .group_tuning import (GRIEVANCE_RETENTION, GROUP_BAN_PULL, GROUP_DISBANDING_SHARE,
						   GROUP_LOG_INTERVAL_YEARS, GROUP_ORGANISING_WEIGHT, GROUP_PULL_SCALE,
						   SCANDAL_PER_PETITION)
from .sector import CONCESSION_PREFIX, Sector, sector_key

# however well protected, public blame never falls below this share of what it would be
BLAME_PROTECTION_FLOOR = 0.15


def pull_of(lost_income: float, territory_revenue: float) -> float:
	"""0..1: the share of the state's attention a group commands for income lost."""
	return 1.0 - math.exp(-max(0.0, lost_income) / territory_revenue / GROUP_PULL_SCALE)


def state_response(pull: float, capacity: float, in_deficit: bool, kind: str,
				   lost_income: float) -> Dict[str, Any]:
	"""What a state of this capacity and purse does about a group with this pull: the sum it
	undertakes to make good, whether it forbids the technique, and the blame that falls on the
	founder. A state in deficit cannot afford to forgo the technique's gains, so it compensates
	(and raises the money from the taxpayers it sees) rather than forbids."""
	reach = pull * capacity
	return {"claim": reach * lost_income,
			"ban": kind == "displaced_producers" and reach >= GROUP_BAN_PULL and not in_deficit,
			"blame": SCANDAL_PER_PETITION * reach}


class InterestGroup(RecordedActor):
	kind = "interest_group"

	def sector_key(self) -> str:
		return sector_key(self.record.group_kind, self.record.subject)

	def organised(self) -> bool:
		return self.record.exited_year is None

	def imitation_candidates(self, world: Any) -> List[str]:
		return []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def advance(self, world: Any) -> None:
		if not self.organised():
			return
		record = self.record
		sector = world.sectors().get(self.sector_key())
		# income still counted as lost: this year's loss, or last year's gross loss as it fades
		fresh = 0.0 if sector is None else sector.lost_income
		gross = max(fresh, (record.lost_income + record.received_last_year) * GRIEVANCE_RETENTION)
		if sector is not None:
			record.cause, record.members = sector.cause, sector.members
			record.grievance = gross / sector.income_base if sector.income_base > 0 else 0.0
		revenue = world.scope_revenue(1.0 if sector is None else sector.scope)
		# what the state paid it, averaged with last year's so a payment does not swing the next year's pull
		paid = world.concession_paid(CONCESSION_PREFIX + self.actor_id)
		self.credit(paid, "compensation from the state")
		record.received_last_year = 0.5 * (record.received_last_year + paid)
		record.lost_income = max(0.0, gross - record.received_last_year)
		if record.lost_income / revenue < GROUP_ORGANISING_WEIGHT * GROUP_DISBANDING_SHARE:
			record.exited_year = world.year
			record.strength = record.claim = 0.0
			record.demands = []
			world.say("%s: no longer organised, the loss has eased (%s)" % (record.name, record.cause))
			return
		record.strength = pull_of(record.lost_income, revenue)
		record.peak_strength = max(record.peak_strength, record.strength)
		response = state_response(record.strength, world.state_capacity(), world.state_in_deficit(),
								  record.group_kind, record.lost_income)
		record.claim = response["claim"]
		record.demands = ["ban the techniques that make " + record.subject] if response["ban"] else []
		blame = response["blame"] * max(BLAME_PROTECTION_FLOOR, 1.0 - world.founder_protection())
		if blame > 0.0:
			record.petitions += 1
			world.lodge_blame(blame, self.words(), GROUP_LOG_INTERVAL_YEARS, record)

	def words(self) -> str:
		"""The log line a petition produces: who, how many, caused by what, asking what."""
		record = self.record
		asks = ["to be made good (%s a year)" % "{:,.0f}".format(record.claim)] if record.claim > 0.5 else []
		asks.extend(record.demands)
		return ("INTEREST GROUP %s petitions the state: about %s people out of pocket %s a year because %s; "
				"they ask %s. The blame lands on you"
				% (record.name, "{:,.0f}".format(record.members), "{:,.0f}".format(record.lost_income),
				   record.cause, " and ".join(asks) if asks else "to be heard"))

	@classmethod
	def founded_by(cls, sector: Sector) -> Dict[str, Any]:
		"""The record fields of a group founded on this sector."""
		return {"kind": "interest_group", "name": sector.name, "group_kind": sector.kind,
				"subject": sector.subject, "cause": sector.cause, "members": sector.members}
