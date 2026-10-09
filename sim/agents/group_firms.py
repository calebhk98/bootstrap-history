"""Owners of firms as an interest group: those whose firms earn less than they have come to expect."""
from typing import Any, List

from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .sector import Sector

FIRM_OWNERS = "firm_owners"


def remember_margins(firms: List[Any]) -> None:
	"""Each year an owner's expectation of a firm's profit moves toward what it earned (at the rate a
	body of people comes to expect its welfare); a firm earning nothing yet expects nothing."""
	for firm in firms:
		record = firm.record
		if record.exited_year is not None:
			continue
		if record.margin_reference <= 0.0:
			record.margin_reference = max(0.0, record.last_margin)
		else:
			record.margin_reference += STRATUM_WELFARE_MEMORY_RATE * (record.last_margin - record.margin_reference)


def firm_owner_sectors(firms: List[Any]) -> List[Sector]:
	"""One sector of the owners of the firms still trading whose profit has fallen below what they
	expected: the profit that fell away, firm by firm (a firm doing better does not set off another's
	loss); one owning household to a firm."""
	lost = expected = 0.0
	losing = 0
	for firm in firms:
		record = firm.record
		if record.exited_year is not None or record.margin_reference <= 0.0:
			continue
		expected += record.margin_reference
		fall = record.margin_reference - record.last_margin
		if fall > 0.0:
			lost += fall
			losing += 1
	if expected <= 0.0 or lost < STRATUM_GRIEVANCE_THRESHOLD * expected:
		return []
	return [Sector(FIRM_OWNERS, "firms", "owners of firms",
				   "the profit of %d firms has fallen %d%% below what their owners had come to expect"
				   % (losing, round(100.0 * lost / expected)), lost, expected, float(losing), 1.0)]
