"""The volume a market traded, as merchants learn it at the year's close (`merchants.learn_year`).

A merchant sizes a cargo to the volume it expects the destination to take (`merchants_shares.room_left`). Under the
search rule set that is what was delivered there. A market that is short delivers little, so on that figure it draws
little cargo and stays short. Under the clearing rule set the figure is what the market would have taken at the
year's price: what was delivered and what its buyers wanted at that price and did not get."""
from typing import Dict, Iterable, Mapping, Tuple

Market = Tuple[str, str]      # (good, area)


def delivered_alone(delivered: Mapping[Market, float], _unmet: Iterable[Tuple[Market, float]]) -> Mapping[Market, float]:
    """What was delivered in each market, as it is."""
    return delivered


def delivered_and_unmet(delivered: Mapping[Market, float], unmet: Iterable[Tuple[Market, float]]) -> Dict[Market, float]:
    """What each market would have taken: its deliveries and the demand left unmet at the year's price (`unmet`: pairs of
    a market and the units its buyers went short of). A market with unmet demand and no delivery is in the answer."""
    volumes = dict(delivered)
    for market, short in unmet:
        if short > 0.0:
            volumes[market] = volumes.get(market, 0.0) + short
    return volumes
