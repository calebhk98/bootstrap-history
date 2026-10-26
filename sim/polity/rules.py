"""Polity's rules as plain functions of plain values: how alarming a technology is, what protects a household, how visible it
is to the state, how consent bounds the state's reach, and how a year moves reputation, familiarity, scandal and bribes."""
import math
from typing import Dict, Iterable, Mapping, Sequence

from . import constants


def legitimacy_share(summed_effects: float, floor: float, ceiling: float) -> float:
	"""The share of its reach the people's consent leaves the state: the works' effects summed, held between the floor
	(force and habit still collect something) and the ceiling (no praise makes a state stronger than that)."""
	return max(floor, min(ceiling, summed_effects))


def state_trait_weights(base_weights: Mapping[str, float], values: Mapping[str, float]) -> Dict[str, float]:
	"""What the state cares about, per trait: the labour market's own weights, then the society's value weights."""
	weights = dict(base_weights)
	weights.update({"military": values["w_military"], "labour_saving": values["w_labour_saving"],
	                "information": values["w_information"], "commerce": values["w_commerce"],
	                "religious_adjacent": constants.STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT * values["w_religious_rigidity"]})
	return weights


def state_interest(traits: Iterable[str], weights: Mapping[str, float]) -> float:
	"""How much the state values a technique with these traits."""
	return sum(weights.get(trait, 0.0) for trait in traits)


def alarm_before_effects(traits: Iterable[str], values: Mapping[str, float], familiarity: float, protection: float) -> float:
	"""How alarming a technology with these traits is to this society, before the works that soften alarm: speed and money
	do not frighten, an effect the society has no category for does; habituation and protection blunt it."""
	alarm = 0.0
	for trait in traits:
		if trait == "inexplicable":
			alarm += constants.ALARM_WEIGHT_INEXPLICABLE * values["w_magic_fear"]
		elif trait == "spectacle":
			alarm += constants.ALARM_WEIGHT_SPECTACLE * values["w_magic_fear"]
		elif trait == "religious_adjacent":
			alarm += constants.ALARM_WEIGHT_RELIGIOUS_ADJACENT * values["w_religious_rigidity"]
		elif trait == "status_threatening":
			alarm += constants.ALARM_WEIGHT_STATUS_THREATENING
		elif trait == "weapon_democratising":
			alarm += constants.ALARM_WEIGHT_WEAPON_DEMOCRATISING
		elif trait == "labour_saving":
			alarm += constants.ALARM_WEIGHT_LABOUR_SAVING * max(0.0, -values["w_labour_saving"])
	alarm *= (1.0 + max(0.0, -values["w_novelty"]))
	alarm *= max(constants.ALARM_FAMILIARITY_FLOOR, 1.0 - familiarity)
	alarm *= max(constants.ALARM_PROTECTION_FLOOR, 1.0 - protection)
	return alarm


def protection_total(works_protection: float, pressed_office: bool, reputation: float, bribes_year_to_date: float,
                     income: float, bribability: float) -> float:
	"""A household's protection: what patrons and the works that protect give (`works_protection`), a pressed civic
	office, reputation and bribery, capped."""
	protection = works_protection
	if pressed_office:
		protection += constants.PRESSED_OFFICE_PROTECTION
	protection += min(constants.REPUTATION_PROTECTION_CAP, reputation / constants.REPUTATION_PROTECTION_SCALE)
	protection += min(constants.BRIBERY_PROTECTION_CAP,
	                  (bribes_year_to_date / (income * constants.BRIBERY_PROTECTION_INCOME_SHARE)) * bribability)
	return min(constants.PROTECTION_CEILING, protection)


def visible_scale(headcount: float, wealth: float, eminence: float, defiance_surcharge: float, eminence_danger: float,
                  wage_of_labourer: float) -> float:
	"""0..1: what an observer can count of a taxpayer's staff, its wealth and (for a person) its prominence, and a surcharge
	for having defied the state."""
	head_share = min(1.0, math.sqrt(max(0.0, headcount) / constants.HOUSEHOLD_HEADCOUNT_SATURATES_AT))
	wealth_share = min(1.0, max(0.0, wealth) / (constants.HOUSEHOLD_WEALTH_SATURATES_AT * wage_of_labourer))
	eminence_share = min(1.0, max(0.0, eminence) / eminence_danger)
	return min(1.0, constants.HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT * head_share + constants.HOUSEHOLD_SCALE_WEALTH_WEIGHT * wealth_share
	           + constants.HOUSEHOLD_SCALE_EMINENCE_WEIGHT * eminence_share + defiance_surcharge)


def reputation_toward_floor(reputation: float, floor: float, retained: float) -> float:
	"""Reputation decays toward what the household is actually known for, not toward zero."""
	return floor + (reputation - floor) * retained


def familiarity_after(adaptation_rate: float, publications: int, years_known: float, ceiling: float,
                      publication_weight: float, tenure_weight: float) -> float:
	"""How unsurprising the household has become: every year known and every visible thing done makes the next less astonishing."""
	return min(ceiling, 1.0 - math.exp(-adaptation_rate * (publication_weight * publications + tenure_weight * years_known)))


def scandal_warning_band(scandal: float, danger: float, said_band: int):
	"""(the band to announce or None, the band said afterwards): scandal is announced past three quarters of the danger line,
	each higher band once, and forgotten below half of it."""
	if scandal > danger * 0.75:
		band = int(scandal / max(1.0, danger * 0.15))
		return (band, band) if band > said_band else (None, said_band)
	if scandal < danger * 0.5:
		return None, 0
	return None, said_band


def transfer_size(spec: Mapping, debt: float, claims: float, hour_price: float) -> float:
	"""The sum a `transfer` spec asks for: a share of the state's debt or of its claims, or a stated sum in labour hours."""
	sized_by = spec.get("of")
	if sized_by == SIZED_BY_DEBT:
		return spec.get("share", 1.0) * debt
	if sized_by == SIZED_BY_CLAIMS:
		return spec.get("share", 1.0) * claims
	return spec.get("labour_hours", 0.0) * hour_price


def concern_levy_due(takings_and_shares: Sequence) -> Dict[str, float]:
	"""{node id: the sum the state takes} from (node id, share, takings) rows, those with something to take."""
	due = {}
	for node_id, share, takings in takings_and_shares:
		if share > 0.0 and takings > 0.0:
			due[node_id] = share * takings
	return due


# what a transfer can be sized by, besides a stated sum
SIZED_BY_DEBT = "debt"
SIZED_BY_CLAIMS = "claims"

