"""A tariff reaches the state that set it as a transfer from the border to its treasury.

Imports are offered at a price that already carries the tariff (the goods market quotes it), so the buyer pays it to
the external edge with the rest of the price. The part of each payment that is duty then goes from the edge to the
state, like any other revenue; a payment for a good no tariff covers carries none."""
from typing import Callable, List, Mapping, Tuple

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


def carried_duty_transfers(carried_value: Mapping[Tuple[AgentId, str], float], tariff_toward: Mapping[str, float],
                           balance_of: Callable[[AgentId], float], state_agent: AgentId, currency: CurrencyId) -> List[Transfer]:
    """One transfer from each carrier to the state for the tariff on the goods it carried in from another country of the
    economy. `carried_value[(carrier, source country)]` is the value of what it carried, at the source, and `tariff_toward[source]`
    the share of that value the state charges; a carrier pays no more than it holds."""
    owed = {}
    for (carrier, source), value in sorted(carried_value.items()):
        tariff = tariff_toward.get(source, 0.0)
        if tariff > 0.0 and value > 0.0 and carrier != state_agent:
            owed[carrier] = owed.get(carrier, 0.0) + tariff * value
    transfers = []
    for carrier, amount in sorted(owed.items()):
        paid = min(amount, max(0.0, balance_of(carrier)))
        if paid > 0.0:
            transfers.append(Transfer(carrier, state_agent, currency, paid, "tax:tariff on carried goods"))
    return transfers
