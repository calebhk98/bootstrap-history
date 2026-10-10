"""How an actor the state presses answers a demand: comply, refuse and take the chance, negotiate a
smaller sum or a service, or conceal wealth so the state sees less to demand of.

The demand is the state's (a requisition, a supply levy, a confiscation). The answer is the actor's, any
actor's. What refusing costs is not scripted: the state enforces with the capacity it has, standing blunts
it, and a state that does enforce takes the demand and a penalty in proportion to that capacity. A
refusal also marks the actor (`defiance`), which makes it more visible to the state. Nothing here names a
civilisation, a commodity or the founder.
"""
from typing import Any, Dict, Tuple

from .tuning_demand import (CONCEALED_SHARE_OF_WEALTH, CONCEALMENT_COST_RATE, CONCEALMENT_DETECTION_SHARE,
							DEFIANCE_MEMORY, DEFIANCE_NOTICE_WEIGHT, DEMAND_STANDING_DISCOUNT, NEGOTIATE_OFFER_SHARE,
							REFUSAL_BLAME_POINTS, REFUSAL_DEFIANCE, REFUSAL_PENALTY_MULTIPLE, STATE_SERVICE_VALUE_SHARE)

COMPLY = "comply"
REFUSE = "refuse"
NEGOTIATE = "negotiate"
CONCEAL = "conceal"
STANCES: Tuple[str, ...] = (COMPLY, REFUSE, NEGOTIATE, CONCEAL)


def _unit(value: float) -> float:
	return max(0.0, min(1.0, value))


def enforcement_chance(capacity: float, standing: float) -> float:
	"""0..1: the chance the state makes a refusal cost. A state enforces what it can reach (its
	capacity) and a patron or standing turns part of that aside."""
	return _unit(capacity) * (1.0 - DEMAND_STANDING_DISCOUNT * _unit(standing))


def negotiation_rejection_chance(capacity: float, standing: float, offered_share: float) -> float:
	"""0..1: the chance the state turns down an offer of this share of its demand. A state that could
	enforce the whole demand takes a small offer ill; one that offers nearly all of it is seldom refused."""
	return enforcement_chance(capacity, standing) * (1.0 - _unit(offered_share))


def settle_demand(stance: str, demanded: float, capacity: float, standing: float, draw: float,
				  service_worth: float = 0.0) -> Dict[str, Any]:
	"""What the actor pays on a demand of `demanded` when it answers with `stance`; `draw` in 0..1 is the
	roll of whether the state enforces a refusal or turns down an offer. `penalty` is the part paid beyond
	the demand; `service` is what the actor spends on a service for the state (of `service_worth` at
	most), which the state counts against the demand; `refused` says the actor defied the state."""
	demanded = max(0.0, demanded)
	settled: Dict[str, Any] = {"paid": demanded, "penalty": 0.0, "enforced": False, "withheld": 0.0,
							   "service": 0.0, "refused": False, "negotiated": False}
	if stance == NEGOTIATE and demanded > 0.0:
		money = NEGOTIATE_OFFER_SHARE * demanded
		service = min(max(0.0, service_worth), (demanded - money) / STATE_SERVICE_VALUE_SHARE)
		offered_share = (money + STATE_SERVICE_VALUE_SHARE * service) / demanded
		if draw >= negotiation_rejection_chance(capacity, standing, offered_share):
			settled.update(paid=money, service=service, negotiated=True)
		return settled
	if stance != REFUSE:
		return settled
	settled["refused"] = demanded > 0.0
	if draw < enforcement_chance(capacity, standing):
		penalty = demanded * _unit(capacity) * REFUSAL_PENALTY_MULTIPLE
		settled.update(paid=demanded + penalty, penalty=penalty, enforced=True)
		return settled
	settled.update(paid=0.0, withheld=demanded)
	return settled


def concealed_target(stance: str, wealth: float) -> float:
	"""The wealth an actor answering with `stance` holds out of the state's sight this year."""
	return CONCEALED_SHARE_OF_WEALTH * max(0.0, wealth) if stance == CONCEAL else 0.0


def visible_wealth(wealth: float, concealed: float) -> float:
	"""The wealth the state can count: what is held less what is hidden."""
	return max(0.0, wealth - max(0.0, concealed))


def settle_concealment(stance: str, wealth: float, capacity: float, standing: float, draw: float) -> Dict[str, float]:
	"""The year's hiding of wealth: `concealed` is what stays out of sight, `cost` what keeping it there
	costs, and `seized` what the state takes (the hoard and a penalty in proportion to its capacity) when
	it finds it, in which case nothing stays hidden."""
	target = concealed_target(stance, wealth)
	if target <= 0.0:
		return {"concealed": 0.0, "cost": 0.0, "seized": 0.0, "found": 0.0}
	if draw < CONCEALMENT_DETECTION_SHARE * enforcement_chance(capacity, standing):
		seized = min(max(0.0, wealth), target * (1.0 + _unit(capacity) * REFUSAL_PENALTY_MULTIPLE))
		return {"concealed": 0.0, "cost": 0.0, "seized": seized, "found": target}
	return {"concealed": target, "cost": CONCEALMENT_COST_RATE * target, "seized": 0.0, "found": 0.0}


def defiance_after_refusal(previous: float) -> float:
	"""0..1: how far the state holds the actor's defiance against it once it has refused a demand."""
	return _unit(previous + REFUSAL_DEFIANCE)


def defiance_fading(previous: float) -> float:
	"""The defiance the state still holds against the actor a year later."""
	return _unit(previous * DEFIANCE_MEMORY)


def notice_surcharge(defiance: float) -> float:
	"""The visible scale the state adds for an actor that has defied it."""
	return DEFIANCE_NOTICE_WEIGHT * _unit(defiance)


def blame_for_refusal(refused: bool) -> float:
	"""The scandal points a refused demand puts on the one who refused."""
	return REFUSAL_BLAME_POINTS if refused else 0.0


def negotiation_odds(demanded: float, capacity: float, standing: float, service_worth: float = 0.0) -> Dict[str, float]:
	"""What the actor can be told before it negotiates: the chance the state takes the offer, what it
	pays then (money and service), and what it pays when the state insists on the whole demand."""
	demanded = max(0.0, demanded)
	money = NEGOTIATE_OFFER_SHARE * demanded
	service = min(max(0.0, service_worth), (demanded - money) / STATE_SERVICE_VALUE_SHARE)
	share = (money + STATE_SERVICE_VALUE_SHARE * service) / demanded if demanded > 0.0 else 1.0
	return {"chance_accepted": 1.0 - negotiation_rejection_chance(capacity, standing, share),
			"money_if_accepted": money, "service_if_accepted": service, "pay_if_insisted": demanded}


def refusal_odds(demanded: float, capacity: float, standing: float) -> Dict[str, float]:
	"""What the actor can be told before it chooses: the chance a refusal is enforced and what it
	then pays against the demand it would otherwise meet."""
	demanded = max(0.0, demanded)
	return {"chance_enforced": enforcement_chance(capacity, standing),
			"pay_if_enforced": demanded * (1.0 + _unit(capacity) * REFUSAL_PENALTY_MULTIPLE),
			"pay_if_not": 0.0, "pay_if_complying": demanded}


def checked_stance(stance: Any) -> str:
	"""The stance named, or a refusal to guess one."""
	if stance not in STANCES:
		raise ValueError("answer with one of: %s" % ", ".join(STANCES))
	return str(stance)
