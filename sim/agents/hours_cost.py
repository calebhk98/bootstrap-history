"""What hours of labour cost at the going quote of the home labour market."""
from typing import Any, Dict, Mapping, Optional


def priced_hours(hours: Mapping[str, float], world: Any) -> Optional[Dict[str, float]]:
	"""{trade: money for its hours at the going quote}, in the order of `hours`; None when any trade has no wage under the economy's rule,
	since the work then has no known cost."""
	priced: Dict[str, float] = {}
	for trade, amount in hours.items():
		quote = world.labour.labour_market.quote(trade)
		if quote is None:
			return None
		priced[trade] = amount * quote
	return priced
