"""The roads and track the engine's actors have built, and what building one costs.

`state.economy.improvements` is {edge key: {"road": true, "rail": true}}, the record geography's
routes read (sim/geography/INTERFACE.md). What a way takes (labour hours and material tonnes) comes
from geography's terrain model; this module prices it at the labour and goods markets and records it.
Nothing here is specific to the founder: it asks for the paying actor's household.

[temporary_heuristic] A way is finished and usable the moment it is paid for; building it takes the
wages and material only, not a time or the labourers' absence from other work.
"""
import sim.geography.api as geography
from sim.agents.api import edges


class WaysMixin:

    def ways_built(self):
        """{edge key: {way: true}} of what has been built, as geography's routes take it."""
        return self.state.economy.improvements

    def way_quote(self, tile_a, tile_b, way):
        """What building `way` ("road", "rail") between two bordering tiles costs now:
        {money, labour_hours, materials, km, node}, or None when it cannot be built there or a material
        has no price."""
        needs = geography.build_requirements(tile_a, tile_b, way, self.world_map)
        if needs is None:
            return None
        money = needs["labour_hours"] * self.labour.labour_market.quote(needs["trade"], needs["labour_hours"])
        for material, tonnes in needs["materials"].items():
            priced = self.goods_market.purchase_cost(material, tonnes)
            if priced is None:
                return None
            money += priced[0]
        return {"money": money, "labour_hours": needs["labour_hours"], "materials": needs["materials"],
                "km": needs["km"], "node": needs["node"]}

    def build_way(self, tile_a, tile_b, way):
        """Build `way` between two bordering tiles the nation holds. Returns (ok, message)."""
        held = set(self.labour.settlement_tiles())
        if tile_a not in held or tile_b not in held:
            return False, "both tiles must be ones your nation holds."
        quote = self.way_quote(tile_a, tile_b, way)
        if quote is None:
            return False, "a %s cannot be built between %s and %s." % (way, tile_a, tile_b)
        known = set(self.state.projects.done) | set(self.state.projects.granted)
        if quote["node"] and quote["node"] not in known:
            return False, "your people do not know how to build a %s yet (%s)." % (way, quote["node"])
        key = geography.edge_key(tile_a, tile_b)
        if self.state.economy.improvements.get(key, {}).get(way):
            return False, "a %s already joins %s and %s." % (way, tile_a, tile_b)
        from . import purchase_rule
        if not purchase_rule.can_pay(self, quote["money"]):
            return False, "a %s of %.0f km costs about %s; %s." % (
                way, quote["km"], "{:,.0f}".format(quote["money"]), purchase_rule.afford_means())
        self.pay_edge(edges.EDGE_BUILDERS, quote["money"], "building a %s" % way)
        self.state.economy.improvements.setdefault(key, {})[way] = True
        return True, "built a %s of %.0f km between %s and %s for %s." % (
            way, quote["km"], tile_a, tile_b, "{:,.0f}".format(quote["money"]))
