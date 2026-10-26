"""A partner quote prices the cargo's own spoilage (Complaints/340): the material is named to the merchants' terms.
`partner_landed_price` (the engine bridge's view of a partner's price) is called on a stub that holds only what it reads."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.bridge_living_stock import partner_landed_price
from sim.world.material_units import tonnes_per_unit

QUICK_TOPIC = True

PARTNER, RAMIE = "han_china_100ad", "ramie_stock_kg"
ROUTE = SimpleNamespace(cost_per_tonne=50.0)


def buyer(named):
    def cost_share(route, material=None, civilization_id=None):
        named.append(material)
        return 0.25

    return SimpleNamespace(
        partner_countries=lambda: [PARTNER], partner_refusal=lambda civilization_id, material: None,
        _foreign_economy_facts=lambda civilization_id: {"prices_in_home_money": {RAMIE: 10.0},
                                                        "solved_materials": [RAMIE], "route": "sea"},
        view=lambda name: {"material_route": lambda civ, material, route: ROUTE, "trader_cost_share": cost_share,
                           "trader_agent_cost": lambda civilization_id, route: 5.0}[name],
        partner_civ=lambda civilization_id: {}, partner_price_level=lambda civilization_id: 1.0)


named = []
quote = partner_landed_price(buyer(named), PARTNER, RAMIE)
check("a partner quote is made", quote is not None and quote > 0, quote)
check("the merchants' terms are asked for the material quoted", named == [RAMIE], named)
check("the quote adds the merchants' share to the price and then the agent's and the route's carriage",
      abs(quote - ((10.0 / tonnes_per_unit(RAMIE)) * 1.25 + 5.0 + 50.0)) < 1e-9, quote)
