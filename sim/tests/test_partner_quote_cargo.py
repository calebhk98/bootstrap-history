"""A partner quote prices the cargo's own spoilage (Complaints/340): the material is named to the merchants' terms."""
from .harness import *  # noqa: F401,F403

HOME, PARTNER, RAMIE = "rome_100ad", "han_china_100ad", "ramie_stock_kg"

buyer = sim(civ=HOME, capital=1e7)
named = []
original_share = buyer._trader_cost_share


def recording_share(route, material=None, civilization_id=None):
    named.append(material)
    return original_share(route, material, civilization_id)


buyer._trader_cost_share = recording_share
quote = buyer.partner_quote_per_tonne(RAMIE, PARTNER)
check("a partner quote is made", quote is not None and quote > 0, quote)
check("the merchants' terms are asked for the material quoted", named == [RAMIE], named)
