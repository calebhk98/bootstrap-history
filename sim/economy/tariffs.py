"""A tariff on goods the economy's own merchants carry in from another country of it reaches the state that set it as a transfer
from the carrier to its treasury. A cargo a trader lands from abroad pays its tariff once, in the cargo leg (foreign_trade/cargo.py)."""
from typing import Callable, List, Mapping, Tuple

from .types import AgentId, CurrencyId, Transfer


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
