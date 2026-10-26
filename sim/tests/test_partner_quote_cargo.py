"""A partner quote prices the cargo's own spoilage (Complaints/340): the material is named to the merchants' terms.
the foreign-trade module's `partner_landed_price` is called over plain views."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.foreign_trade.module import ForeignTrade
from sim.tests import module_harness
from sim.world.material_units import tonnes_per_unit

QUICK_TOPIC = True

PARTNER, RAMIE = "han_china_100ad", "ramie_stock_kg"
ROUTE = SimpleNamespace(cost_per_tonne=50.0)


def buyer(named):
    """The foreign-trade module over a partner whose facts and the merchants' terms are written out."""
    def cost_share(route, material=None, civilization_id=None):
        named.append(material)
        return 0.25

    class Stubbed(ForeignTrade):
        def partner_facts(self, civilization_id):
            return {"prices_in_home_money": {RAMIE: 10.0}, "solved_materials": [RAMIE], "route": "sea"}

        def partner_refusal(self, civilization_id, material):
            return None

        def partner_civ(self, civilization_id):
            return {}

    return module_harness.build(Stubbed, views={
        "foreign_economy_records": [{"civilization": PARTNER, "enabled": True, "from_year": -1000, "until_year": 3000}],
        "year": 100, "civilisation": {"id": "rome_100ad"}, "material_route": lambda civ, material, route: ROUTE,
        "trader_cost_share": cost_share, "trader_agent_cost": lambda civilization_id, route: 5.0,
        "partner_price_level": lambda civilization_id: 1.0})


named = []
quote = buyer(named).partner_landed_price(PARTNER, RAMIE)
check("a partner quote is made", quote is not None and quote > 0, quote)
check("the merchants' terms are asked for the material quoted", named == [RAMIE], named)
check("the quote adds the merchants' share to the price and then the agent's and the route's carriage",
      abs(quote - ((10.0 / tonnes_per_unit(RAMIE)) * 1.25 + 5.0 + 50.0)) < 1e-9, quote)
