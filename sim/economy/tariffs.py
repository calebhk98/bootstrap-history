"""A tariff reaches the state that set it as a transfer from the border to its treasury.

Imports are offered at a price that already carries the tariff (the goods market quotes it), so the buyer pays it to
the external edge with the rest of the price. The part of each payment that is duty then goes from the edge to the
state, like any other revenue; a payment for a good no tariff covers carries none."""
from typing import List, Mapping, Tuple

from .types import EDGE_EXTERNAL, AgentId, CurrencyId, GoodId, Transfer


def duty_transfers(duty_share_of_price: Mapping[GoodId, float], paid_to_border: Mapping[Tuple[AgentId, GoodId], float],
                   state_agent: AgentId, currency: CurrencyId) -> List[Transfer]:
    """One transfer from the external edge to the state for the duty inside what was paid for each good.
    `duty_share_of_price[good]` is the share of that good's landed price that is duty."""
    by_good = {}
    for (_payer, good), paid in sorted(paid_to_border.items()):
        share = duty_share_of_price.get(good, 0.0)
        if share > 0.0 and paid > 0.0:
            by_good[good] = by_good.get(good, 0.0) + paid * share
    return [Transfer(EDGE_EXTERNAL, state_agent, currency, amount, "tax:tariff on " + good)
            for good, amount in sorted(by_good.items()) if amount > 0.0]
