"""How an actor the state presses answers a demand: comply, or refuse and take the chance.

The demand is the state's (a requisition, a supply levy). The answer is the actor's, any actor's. What
refusing costs is not scripted: the state enforces with the capacity it has, standing blunts it, and a
state that does enforce takes the demand and a penalty in proportion to that capacity. Nothing here names
a civilisation, a commodity or the founder.
"""
from typing import Any, Dict, Tuple

from .tuning_demand import DEMAND_STANDING_DISCOUNT, REFUSAL_PENALTY_MULTIPLE

COMPLY = "comply"
REFUSE = "refuse"
# the answers built so far; negotiating and concealing are listed in Complaint 110
STANCES: Tuple[str, ...] = (COMPLY, REFUSE)


def _unit(value: float) -> float:
	return max(0.0, min(1.0, value))


def enforcement_chance(capacity: float, standing: float) -> float:
	"""0..1: the chance the state makes a refusal cost. A state enforces what it can reach (its
	capacity) and a patron or standing turns part of that aside."""
	return _unit(capacity) * (1.0 - DEMAND_STANDING_DISCOUNT * _unit(standing))


def settle_demand(stance: str, demanded: float, capacity: float, standing: float, draw: float) -> Dict[str, Any]:
	"""What the actor pays on a demand of `demanded` when it answers with `stance`; `draw` in 0..1 is the
	roll of whether the state enforces a refusal. `penalty` is the part paid beyond the demand."""
	demanded = max(0.0, demanded)
	if stance != REFUSE:
		return {"paid": demanded, "penalty": 0.0, "enforced": False, "withheld": 0.0}
	if draw < enforcement_chance(capacity, standing):
		penalty = demanded * _unit(capacity) * REFUSAL_PENALTY_MULTIPLE
		return {"paid": demanded + penalty, "penalty": penalty, "enforced": True, "withheld": 0.0}
	return {"paid": 0.0, "penalty": 0.0, "enforced": False, "withheld": demanded}


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
