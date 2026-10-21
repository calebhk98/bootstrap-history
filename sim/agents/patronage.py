"""What a state would give one client in direct funding in a year if its treasury could spare it, for every state and client."""
from typing import Dict, List, Sequence, Tuple


def ask(base: float, output_per_head: float, reach: float, population_scale: float, population_exponent: float,
		governance: float, governance_scale: float, reputation_factor: float) -> float:
	"""The funding a state of this reach and size gives a client: a base sum (money) at the real output per head and reach of
	the state, rising with the size of its people on a sub-linear curve, with the client's governance and with its reputation."""
	return (base * output_per_head * reach * population_scale ** population_exponent
			* (1.0 + max(0.0, governance) / governance_scale) * reputation_factor)


def ask_of_country(terms: Dict[str, float], hour_money: float, output_per_head: float, reach: float,
				   clients: Sequence[Tuple[float, float]]) -> float:
	"""What a country's state is asked for in all, by the clients (governance, reputation factor) of its own: each at the
	country's pay for an hour of work, its real output per head and its reach. `terms` are the funding terms the world holds
	(`base_hours`, `population_scale`, `exponent`, `governance_scale`)."""
	base = terms["base_hours"] * hour_money
	asks: List[float] = [ask(base, output_per_head, reach, terms["population_scale"], terms["exponent"], governance,
							 terms["governance_scale"], reputation) for governance, reputation in clients]
	return sum(asks)

