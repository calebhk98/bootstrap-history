"""A stratum's year: income, needs by tier, growth, schooling, and who decides to move.

Cross-stratum flows (people with their savings, a keeper's allowance) are only decided here or
settled by `settle_strata` after every stratum has had its turn, since a stratum sees no other actor.
"""
import math
from typing import Any, Dict

from . import ledger
from .tuning_strata import (BIRTH_RATE, BIRTH_WELFARE_RESPONSE, BONDAGE_EXIT_RATE, BONDED_BIRTH_SHARE,
							DEATH_RATE, EDUCATION_EFFORT_SCALE, FALL_WELFARE, FAMINE_DEATH_RATE,
							GROWTH_LAG_SHARE, LITERACY_CEILING, LITERACY_DECAY_RATE, LITERACY_GAIN_RATE,
							LITERACY_WIDTH, MOBILITY_RATE, RISE_LITERACY, RISE_WELFARE, STRATUM_EDUCATION_SHARE,
							STRATUM_OTHER_NEED_FOOD_MULTIPLE, STRATUM_SAVINGS_BUFFER_YEARS,
							STRATUM_WORKING_SHARE, WELFARE_WIDTH)

TIERS = ("food", "housing", "goods")


def logistic(value: float) -> float:
	if value < -60.0:
		return 0.0
	return 1.0 / (1.0 + math.exp(-value))


def own_income(stratum: Any, world: Any) -> float:
	"""What the stratum earns by its own wages and property: nothing for the bonded."""
	plan = stratum.record.plan
	if stratum.is_bonded():
		return 0.0
	income = 0.0
	trade = plan.get("trade")
	if trade:
		working = float(plan.get("work_share", STRATUM_WORKING_SHARE))
		wages = stratum.record.members * working * world.pay_per_person_year(trade)
		if plan.get("own_plot"):
			# people with land earn at least what keeps those they support fed, from their own plot when
			# no employer pays that much: the classical floor under wages the agent economy also uses
			wages = max(wages, stratum.record.members * world.subsistence_cost_per_person_year())
		income += wages
	property_share = float(plan.get("property_share") or 0.0)
	if property_share > 0.0:
		income += world.society_output() * property_share
	return income


def pay_tier(stratum: Any, need: float, spendable: float) -> float:
	"""Buy what can be bought of one tier from `spendable`; the money leaves the modelled actors."""
	paid = max(0.0, min(need, spendable))
	if paid > 0.0:
		stratum.debit(paid, "edge:economy")
	return paid


def unmet(need: float, paid: float) -> float:
	return 0.0 if need <= 0.0 else max(0.0, 1.0 - paid / need)


def run_year(stratum: Any, world: Any) -> None:
	record = stratum.record
	observed: Dict[str, Any] = world.observed_stratum(record.country, record.stratum) or {}
	previous_members = record.members
	if observed.get("members") is not None:
		record.members = float(observed["members"])
	members = record.members
	income = float(observed["income"]) if observed.get("income") is not None else own_income(stratum, world)
	if income > 0.0:
		stratum.credit(income, "edge:economy")
	resources = income + record.allowance
	record.allowance = 0.0
	food_cost = world.subsistence_cost_per_person_year()
	housing_cost = world.housing_cost_per_person_year()
	needs = {"food": members * food_cost, "housing": members * housing_cost,
			 "goods": members * food_cost * STRATUM_OTHER_NEED_FOOD_MULTIPLE}
	buffer = 0.0 if stratum.is_bonded() else STRATUM_SAVINGS_BUFFER_YEARS * (needs["food"] + needs["housing"])
	for tier in TIERS:
		spendable = stratum.money - (buffer if tier == "goods" else 0.0)
		record.shortfall[tier] = unmet(needs[tier], pay_tier(stratum, needs[tier], spendable))
	food_bill = members * food_cost
	record.welfare = resources / food_bill if food_bill > 0.0 else 0.0
	school(stratum, max(0.0, resources - sum(needs.values())), food_bill, buffer)
	if observed.get("members") is not None:
		record.last_growth = record.members / previous_members - 1.0 if previous_members > 0.0 else 0.0
		return
	grow(stratum)
	decide_moves(stratum)


def school(stratum: Any, surplus: float, food_bill: float, buffer: float) -> None:
	"""Spend a share of the surplus on schooling and move literacy toward the ceiling, or let it fade."""
	record = stratum.record
	spend = min(STRATUM_EDUCATION_SHARE * surplus, max(0.0, stratum.money - buffer))
	if spend > 0.0:
		stratum.debit(spend, "edge:economy")
	effort = spend / food_bill if food_bill > 0.0 else 0.0
	funded = 1.0 - math.exp(-effort / EDUCATION_EFFORT_SCALE)
	gain = LITERACY_GAIN_RATE * max(0.0, LITERACY_CEILING - record.literacy) * funded
	loss = LITERACY_DECAY_RATE * record.literacy * (1.0 - funded)
	record.literacy = min(1.0, max(0.0, record.literacy + gain - loss))


def grow(stratum: Any) -> None:
	"""Births rise gently with welfare, deaths rise steeply with the food unmet; growth follows with a lag."""
	record = stratum.record
	birth_rate = BIRTH_RATE * (BONDED_BIRTH_SHARE if stratum.is_bonded() else 1.0)
	births = birth_rate * (1.0 + BIRTH_WELFARE_RESPONSE * math.tanh(record.welfare - 1.0))
	deaths = DEATH_RATE + FAMINE_DEATH_RATE * record.shortfall.get("food", 0.0)
	record.last_growth += GROWTH_LAG_SHARE * ((births - deaths) - record.last_growth)
	record.members = max(0.0, record.members * (1.0 + record.last_growth))


def decide_moves(stratum: Any) -> None:
	"""Name the share of members who rise or fall to another stratum; settled after every turn."""
	record = stratum.record
	record.moving = {}
	literate = logistic((record.literacy - RISE_LITERACY) / LITERACY_WIDTH)
	if stratum.is_bonded():
		rise = BONDAGE_EXIT_RATE * literate
	else:
		rise = MOBILITY_RATE * logistic((record.welfare - RISE_WELFARE) / WELFARE_WIDTH) * literate
	fall = MOBILITY_RATE * logistic((FALL_WELFARE - record.welfare) / WELFARE_WIDTH)
	if record.members <= 0.0:
		return
	for key, share in (("rises_to", rise), ("falls_to", fall)):
		target = record.plan.get(key)
		if target and share > 0.0:
			target_id = stratum.neighbour_id(str(target))
			record.moving[target_id] = record.moving.get(target_id, 0.0) + record.members * share


def settle_moves(registry: Any) -> None:
	"""Carry out the decided moves: people go with their share of the savings and their literacy."""
	for actor in registry.of_kind("stratum"):
		record = actor.record
		for target_id, people in sorted(record.moving.items()):
			target = registry.actors.get(target_id)
			if target is None or target is actor or record.members <= 0.0:
				continue
			people = min(people, record.members)
			ledger.transfer(actor, target, actor.money * people / record.members, "migration")
			combined = target.record.members + people
			target.record.literacy = (target.record.literacy * target.record.members + record.literacy * people) / combined
			target.record.members = combined
			record.members -= people
		record.moving = {}


def settle_keep(registry: Any, world: Any) -> None:
	"""Each keeper stratum pays the food of the bonded it holds for the coming year."""
	for actor in registry.of_kind("stratum"):
		if not actor.is_bonded():
			continue
		owner = registry.actors.get(actor.neighbour_id(str(actor.record.plan.get("owner") or "")))
		if owner is None or owner is actor:
			continue
		cost = actor.record.members * registry.world_for(actor, world).subsistence_cost_per_person_year()
		ledger.transfer(owner, actor, cost, "keep of bonded")
		actor.record.allowance += cost


def settle_strata(registry: Any, world: Any) -> None:
	settle_moves(registry)
	settle_keep(registry, world)
