"""A charge the acting seat cannot pay is logged with its cause, never dropped."""
from typing import Any, Callable

from sim.refusal import cause_of
from sim.reporting.api import RecordEvent

from .commands import PayEdge

UNPAID_CHARGE_KIND = "unpaid_charge"


def pay_edge_or_log(send: Callable[[Any], Any], edge: str, amount: float, purpose: Any) -> bool:
	"""Send the acting seat's payment to an edge: True when paid. A refusal is logged as an `unpaid_charge` event (the edge,
	the amount, the purpose and the refusal's cause as facts) and False comes back, so the caller does not book the charge
	as paid or go on with what it was to pay for."""
	refusal = send(PayEdge(edge, amount, purpose))
	if refusal is None:
		return True
	send(RecordEvent.of(UNPAID_CHARGE_KIND, "could not pay %s: %s" % (purpose, refusal),
	                    edge=edge, amount=amount, purpose=str(purpose), cause=cause_of(refusal)))
	return False
