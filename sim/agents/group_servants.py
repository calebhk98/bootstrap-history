"""The state's own servants as interest groups: office-holders paid salaries and fees, and an army paid from its budget line.

Both are read from the state's budget (`Government.record.need` and `.unfunded` by line, its revenue through the
world), not from a table of their own. Office-holders expect what they have come to be paid in salary and fees;
a cut in the salary lines or a fall in the revenue their fees come from is their loss. An army that goes unpaid
loses its loyalty, and an army without loyalty acts on the state: soldiers desert and the rest take their back
pay from the treasury (`mutiny`).
"""
from typing import Any, Dict, List

from . import budget, ledger
from .edges import EDGE_STATE_SPENDING
from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .group_tuning_stakes import (DESERTION_RATE, LOYALTY_ADJUSTMENT_RATE, MUTINY_LOYALTY, OFFICE_FEE_SHARE_OF_REVENUE)
from .registry import register_spawner
from .sector import Sector

OFFICE_HOLDERS = "office_holders"
SOLDIERS = "soldiers"
SALARIES = "salaries"
FEES = "fees"
# the budget lines that pay people in office
SALARY_LINES = ("administration", "court")
ARMY_LINE = "army"


def salaries_paid(record: Any) -> float:
	"""What the state paid last year on the lines that pay its officials."""
	return sum(max(0.0, record.need.get(name, 0.0) - record.unfunded.get(name, 0.0)) for name in SALARY_LINES)


def office_income(government: Any, world: Any) -> Dict[str, float]:
	"""What the state's office-holders took last year: the salaries it paid and the fees they keep from the
	revenue that passes through their hands (TEMPORARY HEURISTIC, CLAUDE.md 4.4: a share of the state's
	revenue until fees are a form of revenue of their own)."""
	return {SALARIES: salaries_paid(government.record), FEES: OFFICE_FEE_SHARE_OF_REVENUE * world.state_revenue()}


def remember_servants(government: Any, world: Any) -> None:
	"""Each year what the office-holders expect moves toward what they took (at the rate a body of people
	comes to expect its welfare)."""
	record = government.record
	for line, amount in office_income(government, world).items():
		reference = record.income_reference.get(line, 0.0)
		record.income_reference[line] = amount if reference <= 0.0 else reference + STRATUM_WELFARE_MEMORY_RATE * (amount - reference)


def servant_sectors(government: Any, world: Any) -> List[Sector]:
	"""The state's servants who are out of pocket: office-holders when salaries paid and fees taken are below
	what they expected, soldiers when the army's line goes partly unpaid (their back pay is the loss)."""
	record = government.record
	sectors = []
	income = office_income(government, world)
	falls = {line: record.income_reference.get(line, 0.0) - amount for line, amount in income.items()
			 if record.income_reference.get(line, 0.0) > 0.0 and record.income_reference.get(line, 0.0) - amount > 0.0}
	expected = sum(record.income_reference.values())
	if expected > 0.0 and sum(falls.values()) >= STRATUM_GRIEVANCE_THRESHOLD * expected:
		words = ", ".join("%s %d%% below what they had come to expect" % (line, round(100.0 * fall / record.income_reference[line]))
						  for line, fall in sorted(falls.items()))
		unpaid = sum(record.unfunded.get(name, 0.0) for name in SALARY_LINES)
		if unpaid > 0.0:
			words += " (%s of the state's pay unpaid)" % world.money_text(unpaid, grouped=True)
		sectors.append(Sector(OFFICE_HOLDERS, "administration", "the state's office-holders",
							  "what they take from the state has fallen: " + words,
							  sum(falls.values()), expected, budget.officials_kept(world), 1.0))
	due = record.need.get(ARMY_LINE, 0.0)
	unpaid = record.unfunded.get(ARMY_LINE, 0.0)
	if due > 0.0 and unpaid > 0.0:
		sectors.append(Sector(SOLDIERS, "army", "the state's soldiers",
							  "the army's pay is %d%% in arrears" % round(100.0 * unpaid / due),
							  unpaid, due, record.army * unpaid / due, 1.0))
	return sectors


def step_loyalty(loyalty: float, unpaid_share: float) -> float:
	"""0..1: the army's loyalty a year on; it moves toward the share of its pay it got."""
	target = max(0.0, min(1.0, 1.0 - unpaid_share))
	return max(0.0, min(1.0, loyalty + LOYALTY_ADJUSTMENT_RATE * (target - loyalty)))


def mutiny(loyalty: float, soldiers: float, arrears: float, treasury: float) -> Dict[str, float]:
	"""What an army with this loyalty does to the state: below the mutiny line, soldiers desert in proportion to
	how far below it is, and the rest take as much of their arrears as the treasury holds."""
	if loyalty >= MUTINY_LOYALTY or soldiers <= 0.0:
		return {"deserters": 0.0, "seized": 0.0, "severity": 0.0}
	severity = (MUTINY_LOYALTY - loyalty) / MUTINY_LOYALTY
	return {"deserters": soldiers * DESERTION_RATE * severity,
			"seized": min(max(0.0, treasury), max(0.0, arrears) * severity), "severity": severity}


def run_army_year(government: Any, world: Any) -> Dict[str, float]:
	"""The year's turn of the army's loyalty and, when it has none left, of its mutiny against the state."""
	record = government.record
	due = record.need.get(ARMY_LINE, 0.0)
	arrears = record.unfunded.get(ARMY_LINE, 0.0)
	record.loyalty = step_loyalty(record.loyalty, arrears / due if due > 0.0 else 0.0)
	acted = mutiny(record.loyalty, record.army, arrears, government.money)
	if acted["severity"] > 0.0:
		record.army = max(0.0, record.army - acted["deserters"])
		if acted["seized"] > 0.0:
			ledger.transfer(government, world.edge(EDGE_STATE_SPENDING), acted["seized"], "mutineers take their arrears")
		world.say("MUTINY: the army, unpaid, has lost its loyalty; %s soldiers desert and the rest take %s from the treasury"
				  % (world.plain_number(acted["deserters"]), world.money_text(acted["seized"], grouped=True)))
	return acted


def run_servants(registry: Any, world: Any) -> List[str]:
	"""Each year, for the home state (the government whose country is the founder's): the army's loyalty and mutiny."""
	moved = []
	for government in registry.of_kind("government"):
		if government.record.country is None and government.record.exited_year is None:
			run_army_year(government, world)
			moved.append(government.actor_id)
	return moved


register_spawner("state_servants", run_servants)
