"""What a country's state asks of the engine when it funds the clients of its own: the seats it patronises, the terms of the
funding and the country's real output per head (mixed into `ActorWorld`; the home state's ask is `Sim.patron_funding_ask`)."""
from typing import Any, Dict, List, Optional, Tuple

from sim.reporting.api import output_rules


class PatronageView:
	"""Read-only questions behind a country's patronage."""

	needs: Any

	def patron_clients(self, country: str) -> List[Tuple[float, float]]:
		"""(governance, reputation factor) of the playing seats of `country` whose techniques run the `state_funding` mechanic."""
		return [(governance, reputation) for _seat, governance, reputation in self.needs.patron_clients[country]]

	def state_funding_terms(self, people: float) -> Dict[str, float]:
		"""The terms a state funds a client on, for a country of `people`: the labour hours of the base sum, the exponent of
		the country's size, its size against the reference one, and the scale of the client's governance."""
		constant = self.needs.legacy_constant
		return {"base_hours": constant["STATE_FUNDING_BASE_LABOUR_HOURS"], "exponent": constant["STATE_FUNDING_POP_SCALE_EXPONENT"],
				"governance_scale": constant["STATE_FUNDING_GOV_QUALITY_SCALE"],
				"population_scale": max(constant["POP_SCALE_FLOOR"], people / constant["DEFAULT_POPULATION_100AD"])}

	def country_output_per_head(self, country: str, opening_people: float, people: float) -> Optional[float]:
		"""A country's real output per person over its opening's (one at the baseline), as the economy's markets over its tiles
		closed last year: its traded quantities of the opening basket's goods at the opening prices, as at home
		(`sim/reporting/output.py`), over what its opening basket was worth, and over its people against its opening people. Goods the
		opening basket did not hold are not counted. None while the economy has no record of the country or no people."""
		needs = self.needs
		opened = needs.country_opening_basket[country]
		if opened is None or not opening_people > 0.0 or not people > 0.0:
			return None
		units, prices = opened
		basket = {"prices": prices, "units": {good: wanted for good, wanted in sorted(units.items())
											  if wanted > 0.0 and prices.get(good, 0.0) > 0.0}}
		traded, scale = output_rules.traded_measure(
			basket, needs.country_volume_baseline[country] or {}, needs.country_traded_volumes[country] or {})
		opening = sum(basket["units"][good] * basket["prices"][good] for good in traded)
		if not opening > 0.0:
			return None
		real = sum(units_sold * scale * basket["prices"][good] for good, units_sold in traded.items())
		return real / opening / (people / opening_people)
