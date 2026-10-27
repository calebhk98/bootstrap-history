"""The roads, track, canals, bridges and ports the game's actors have built, and what building one costs.

`LandWorld.improvements` is {key: {"road": true, "rail": true, "canal": true, "bridge": true, "port": true, "engineered":
true}}, the record geography's routes read (sim/geography/INTERFACE.md): a way, canal or bridge under an edge key, a port
under its tile id. What a way takes (labour hours, material tonnes, the crew it works with) comes from geography's terrain
model; this module prices it at the labour and goods markets and records it. Nothing here is specific to the founder: the
acting seat's household pays.

A way is paid for when it is started and becomes usable when its build time has passed: the labour over what the crew works in
a year, where the crew is the people the labour market finds of the way's trade (at most the crew the work calls for). The crew
leans on that trade's pool every year of the build, so other employers pay more for it, and the hands go back when the way
opens. A canal across a declared isthmus is a way like the rest.
"""
from typing import Any, Dict, Optional, Tuple

from sim.agents.api import edges
from sim.geography import api as geography
from sim.ledger.api import PayEdge
from sim.refusal import Refusal

from . import ways_rules
from .commands import BuildWay, FinishWays


class Ways:
    """Mixed into `Land`."""

    needs: Any
    world: Any
    world_map: Any

    def built_ways(self) -> Dict[str, Dict[str, bool]]:
        """The ways built, by way key (the record itself)."""
        return self.world.improvements

    def built_way_km(self, way: str) -> float:
        """Kilometres of `way` the record holds."""
        return geography.built_km(self.world.improvements, way, self.world_map)

    def way_crew(self, needs: Dict[str, Any]) -> Tuple[int, float]:
        """The crew the labour market finds for a way: whole people of its trade, at most the crew the work calls for, and the
        hours a year they work."""
        found = self.needs.labour_market().whole_recruits(needs["trade"], needs["crew_people"])
        return found, ways_rules.crew_hours_a_year(found, needs["crew_hours_per_year"], needs["crew_people"])

    def way_quote(self, tile_a: str, tile_b: str, way: str) -> Optional[Dict[str, Any]]:
        """What building `way` ("road", "rail", "canal", "bridge", or "port" on one tile) between two bordering tiles costs now:
        {money, labour_hours, materials, km, node, years, engineered, trade, crew, crew_hours}, or None when it cannot be built
        there or a material has no price."""
        needs = geography.build_requirements(tile_a, tile_b, way, self.world_map)
        if needs is None:
            return None
        hourly_rate = self.needs.labour_market().quote(needs["trade"], needs["labour_hours"])
        bills = []
        for material, tonnes in needs["materials"].items():
            priced = self.needs.purchase_quote(material, tonnes)
            if priced is None:
                return None
            bills.append(priced[0])
        crew, crew_hours = self.way_crew(needs)
        return {"money": ways_rules.way_money(needs["labour_hours"], hourly_rate, bills), "labour_hours": needs["labour_hours"],
                "materials": needs["materials"], "km": needs["km"], "node": needs["node"],
                "years": ways_rules.way_years(needs["labour_hours"], crew_hours), "engineered": needs["engineered"],
                "trade": needs["trade"], "crew": crew, "crew_hours": crew_hours}

    def way_refusal(self, tile_a: str, tile_b: str, way: str) -> Refusal:
        """Why `way` cannot be built between the tiles: no isthmus declared there for a cut that joins two seas, otherwise that
        the ground or the edge does not allow it."""
        place = ways_rules.where(tile_a, tile_b)
        if geography.is_cut_way(way, self.world_map):
            return Refusal("no_isthmus", "no isthmus is known %s: a %s needs a neck of land between two seas "
                           "that the map says can be cut." % (place, way), way=way)
        return Refusal("cannot_build", "a %s cannot be built %s." % (way, place), way=way)

    def build_way(self, command: BuildWay) -> Tuple[bool, Any]:
        """Build `way` between two bordering tiles the nation holds (a port: on one tile, named twice). Answers (ok, text)."""
        needs = self.needs
        tile_a, tile_b, way = command.tile_a, command.tile_b, command.way
        refusal = ways_rules.not_held_refusal(set(needs.settlement_tiles()), tile_a, tile_b)
        if refusal:
            return False, refusal
        place = ways_rules.where(tile_a, tile_b)
        quote = self.way_quote(tile_a, tile_b, way)
        if quote is None:
            return False, self.way_refusal(tile_a, tile_b, way)
        key = geography.improvement_key(way, tile_a, tile_b, self.world_map)
        refusal = ways_rules.start_refusal(
            way, place, quote, set(needs.techniques_held()) | set(needs.techniques_granted()),
            self.world.improvements.get(key, {}).get(way), way in self.world.ways_under_construction.get(key, {}))
        if refusal:
            return False, refusal
        if not needs.can_pay(quote["money"]):
            return False, "a %s of %.1f km costs about %s; %s." % (
                way, quote["km"], needs.money_text(quote["money"], grouped=True), needs.afford_means())
        needs.send(PayEdge(edges.EDGE_BUILDERS, quote["money"], "building a %s" % way))
        year = needs.year()
        needs.labour_market().hire(None, quote["trade"], quote["crew_hours"])
        self.world.ways_under_construction.setdefault(key, {})[way] = ways_rules.pending_way(year, quote)
        return True, "started a %s of %.1f km %s for %s%s; a crew of %d will take about %.1f years." % (
            way, quote["km"], place, needs.money_text(quote["money"], grouped=True),
            ", engineered through steep ground" if quote["engineered"] else "", quote["crew"], quote["years"])

    def finish_ways(self, command: FinishWays) -> None:
        """Open the ways whose build time has passed, so routes, reach and the economy's carriage see them; the crews of those
        still building lean on their trade's pool again this year; the works register finishes on the same beat."""
        market = self.needs.labour_market()
        for call, trade, hours in ways_rules.open_ways(self.world.ways_under_construction, self.world.improvements,
                                                       self.needs.year()):
            if call == "release":
                market.release(None, trade, hours)
            else:
                market.press(trade, hours)
        self.finish_works()
