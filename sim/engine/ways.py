"""The roads, track, canals, bridges and ports the engine's actors have built, and what building one costs.

`state.economy.improvements` is {key: {"road": true, "rail": true, "canal": true, "bridge": true,
"port": true, "engineered": true}}, the record geography's routes read (sim/geography/INTERFACE.md): a
way, canal or bridge under an edge key, a port under its tile id. What a way takes (labour hours, material
tonnes, the crew it works with) comes from geography's terrain model; this module prices it at the labour
and goods markets and records it. Nothing here is specific to the founder: it asks for the paying
actor's household.

A way is paid for when it is started and becomes usable when its build time has passed: the labour over
what the crew works in a year, where the crew is the people the labour market finds of the way's trade
(at most the crew the work calls for). The crew leans on that trade's pool every year of the build, so
other employers pay more for it, and the hands go back when the way opens.
"""
import sim.geography.api as geography
from sim.agents.api import edges


class WaysMixin:

    def ways_built(self):
        """{edge key: {way: true}} of what has been built, as geography's routes take it."""
        return self.state.economy.improvements

    def built_way_km(self, way):
        """Kilometres of `way` this actor's record holds."""
        return geography.built_km(self.state.economy.improvements, way, self.world_map)

    def _way_crew(self, needs):
        """The crew the labour market finds for a way: whole people of its trade, at most the crew the work
        calls for, and the hours a year they work."""
        found = self.labour.labour_market.whole_recruits(needs["trade"], needs["crew_people"])
        hours_each = needs["crew_hours_per_year"] / needs["crew_people"]
        return found, found * hours_each

    def way_quote(self, tile_a, tile_b, way):
        """What building `way` ("road", "rail", "canal", "bridge", or "port" on one tile) between two
        bordering tiles costs now: {money, labour_hours, materials, km, node, years, engineered, trade,
        crew_hours}, or None when it cannot be built there or a material has no price."""
        needs = geography.build_requirements(tile_a, tile_b, way, self.world_map)
        if needs is None:
            return None
        money = needs["labour_hours"] * self.labour.labour_market.quote(needs["trade"], needs["labour_hours"])
        for material, tonnes in needs["materials"].items():
            priced = self.goods_market.purchase_cost(material, tonnes)
            if priced is None:
                return None
            money += priced[0]
        crew, crew_hours = self._way_crew(needs)
        return {"money": money, "labour_hours": needs["labour_hours"], "materials": needs["materials"],
                "km": needs["km"], "node": needs["node"], "years": needs["labour_hours"] / crew_hours,
                "engineered": needs["engineered"], "trade": needs["trade"], "crew": crew,
                "crew_hours": crew_hours}

    @staticmethod
    def _where(way, tile_a, tile_b):
        return "on %s" % tile_a if tile_a == tile_b else "between %s and %s" % (tile_a, tile_b)

    def build_way(self, tile_a, tile_b, way):
        """Build `way` between two bordering tiles the nation holds (a port: on one tile, named twice).
        Returns (ok, message)."""
        held = set(self.labour.settlement_tiles())
        if tile_a not in held or tile_b not in held:
            return False, "both tiles must be ones your nation holds."
        where = self._where(way, tile_a, tile_b)
        quote = self.way_quote(tile_a, tile_b, way)
        if quote is None:
            return False, "a %s cannot be built %s." % (way, where)
        known = set(self.state.projects.done) | set(self.state.projects.granted)
        if quote["node"] and quote["node"] not in known:
            return False, "your people do not know how to build a %s yet (%s)." % (way, quote["node"])
        key = geography.improvement_key(way, tile_a, tile_b, self.world_map)
        if self.state.economy.improvements.get(key, {}).get(way):
            return False, "a %s already stands %s." % (way, where)
        if way in self.state.economy.ways_under_construction.get(key, {}):
            return False, "a %s %s is already being built." % (way, where)
        from . import purchase_rule
        if not purchase_rule.can_pay(self, quote["money"]):
            return False, "a %s of %.1f km costs about %s; %s." % (
                way, quote["km"], "{:,.0f}".format(quote["money"]), purchase_rule.afford_means())
        self.pay_edge(edges.EDGE_BUILDERS, quote["money"], "building a %s" % way)
        year = self.state.scenario.year
        self.labour.labour_market.hire(self.state.household, quote["trade"], quote["crew_hours"])
        self.state.economy.ways_under_construction.setdefault(key, {})[way] = {
            "due": year + quote["years"], "trade": quote["trade"], "crew_hours": quote["crew_hours"],
            "engineered": quote["engineered"], "pressed": year}
        return True, "started a %s of %.1f km %s for %s%s; a crew of %d will take about %.1f years." % (
            way, quote["km"], where, "{:,.0f}".format(quote["money"]),
            ", engineered through steep ground" if quote["engineered"] else "", quote["crew"], quote["years"])

    def finish_ways(self):
        """Open the ways whose build time has passed, so routes, reach and the economy's carriage see them;
        the crews of those still building lean on their trade's pool again this year; the works register
        (works.py) finishes on the same beat."""
        pending = self.state.economy.ways_under_construction
        market = self.labour.labour_market
        year = self.state.scenario.year
        for key in sorted(pending):
            for way in sorted(pending[key]):
                build = pending[key][way]
                if build["due"] <= year:
                    built = self.state.economy.improvements.setdefault(key, {})
                    built[way] = True
                    if build["engineered"]:
                        built["engineered"] = True
                    market.release(self.state.household, build["trade"], build["crew_hours"])
                    del pending[key][way]
                elif build["pressed"] < year:
                    market.press(build["trade"], build["crew_hours"])
                    build["pressed"] = year
            if not pending[key]:
                del pending[key]
        self.finish_works()
