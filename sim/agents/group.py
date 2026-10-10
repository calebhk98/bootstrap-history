"""`InterestGroup`: people who share a loss and act on the state about it.

A group exists while the income its members lost to one cause stays above what it takes to
organise. Its pull on the state grows with that loss as a share of the revenue of the territory
it lives in. The state answers by what it can do (`state_response`): make the loss good from its
purse, forbid the technique if it can afford to forgo the gains, and let the blame fall on the
founder either way. Nothing here names a trade, a commodity or a civilisation.
"""
import math
from typing import Any, Dict, List

from . import ledger
from .base import RecordedActor
from .edges import EDGE_STATE_SPENDING
from .group_tuning import (GRIEVANCE_RETENTION, GROUP_BAN_PULL, GROUP_CLAIM_CEILING_SHARE, GROUP_DISBANDING_SHARE,
						   GROUP_LOG_INTERVAL_YEARS, GROUP_ORGANISING_WEIGHT, GROUP_PULL_SCALE,
						   SCANDAL_PER_PETITION)
from .sector import CONCESSION_PREFIX, Sector, sector_key

# however well protected, public blame never falls below this share of what it would be
BLAME_PROTECTION_FLOOR = 0.15


def pull_of(lost_income: float, territory_revenue: float) -> float:
	"""0..1: the share of the state's attention a group commands for income lost."""
	return 1.0 - math.exp(-max(0.0, lost_income) / territory_revenue / GROUP_PULL_SCALE)


def state_response(pull: float, capacity: float, in_deficit: bool, kind: str,
				   lost_income: float, territory_revenue: float = float("inf")) -> Dict[str, Any]:
	"""What a state of this capacity and purse does about a group with this pull: the sum it
	undertakes to make good, whether it forbids the technique, and the blame that falls on the
	founder. A state in deficit cannot afford to forgo the technique's gains, so it compensates
	(and raises the money from the taxpayers it sees) rather than forbids."""
	reach = pull * capacity
	return {"claim": min(reach * lost_income, GROUP_CLAIM_CEILING_SHARE * territory_revenue),
			"ban": kind == "displaced_producers" and reach >= GROUP_BAN_PULL and not in_deficit,
			"blame": SCANDAL_PER_PETITION * reach}


def blame_after_protection(blame: float, protection: float, blame_share: float) -> float:
	"""The blame that lands on the founder: his share of the loss, less what his protection turns aside."""
	return blame * blame_share * max(BLAME_PROTECTION_FLOOR, 1.0 - protection)


def protection_needed(group_strength: float, opposition_line: float) -> float:
	"""The protection that lets the founder build despite a prohibition a group of this pull obtained:
	the state-opposition line for a group with no pull, rising toward full protection as its pull grows."""
	return opposition_line + (1.0 - opposition_line) * max(0.0, min(1.0, group_strength))


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
			record.cause, record.members, record.blame_share = sector.cause, sector.members, sector.blame_share
			record.grievance = gross / sector.income_base if sector.income_base > 0 else 0.0
		revenue = world.scope_revenue(1.0 if sector is None else sector.scope)
		# what the state paid it, averaged with last year's so a payment does not swing the next year's pull
		paid = world.concession_paid(CONCESSION_PREFIX + self.actor_id)
		ledger.transfer(world.edge(EDGE_STATE_SPENDING), self, paid, "compensation from the state")
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
								  record.group_kind, record.lost_income, revenue)
		record.claim = response["claim"]
		record.demands = ["ban the techniques that make " + record.subject] if response["ban"] else []
		blame = blame_after_protection(response["blame"], world.founder_protection(), record.blame_share)
		if blame > 0.0:
			record.petitions += 1
			world.lodge_blame(blame, self.words(world), GROUP_LOG_INTERVAL_YEARS, record)

	def words(self, world: Any) -> str:
		"""The log line a petition produces: who, how many, caused by what, asking what."""
		record = self.record
		asks = ["to be made good (%s a year)" % world.money_text(record.claim, grouped=True)] if record.claim > 0.5 else []
		asks.extend(record.demands)
		return ("INTEREST GROUP %s petitions the state: about %s people out of pocket %s a year because %s; "
				"they ask %s. The blame lands on you"
				% (record.name, world.plain_number(record.members), world.money_text(record.lost_income, grouped=True),
				   record.cause, " and ".join(asks) if asks else "to be heard"))

	@classmethod
	def founded_by(cls, sector: Sector) -> Dict[str, Any]:
		"""The record fields of a group founded on this sector."""
		return {"kind": "interest_group", "name": sector.name, "group_kind": sector.kind,
				"subject": sector.subject, "cause": sector.cause, "members": sector.members}
