"""Settled colonies: tiles a seat holds beyond its country's own, each with a people of its own.

A work declares `mechanics.settlement = {"settlers": n, "outfit_hours_per_settler": h, "by_sea": bool}`. Once a seat
knows one, it can found a colony on a tile that borders what it holds (or, by sea, a coastal tile when it holds a coastal
one): the settlers leave the home country's working age and the outfit is paid at the society's wage. The colony's people
are three age cohorts stepped each year by the same demography as the home country's (`sim/world/demography.py`),
fed by the tile's land in the share its working-age people can hold, as many hectares each as a farm worker holds at
home. A colony whose people die out is lost.
"""
from typing import Any, Dict, List, Optional, Tuple

from sim.agents.api import edges
from sim.demography.api import SendSettlers
from sim.geography.api import settlement, tile_owners
from sim.ledger.api import PayEdge
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.world import demography
from sim.world.farm_labour import REFERENCE_LABOUR_HOURS_PER_HECTARE
from sim.world.shared_constants import ANNUAL_LABOUR_HOURS_PER_FARM_WORKER, FALLOW_SHARE_OF_HOLDING

from . import rules
from .commands import FoundColony

# land one farm worker holds, fallow included: the hours a worker gives a year over the hours a cropped hectare takes
HOLDING_HECTARES_PER_WORKER = (ANNUAL_LABOUR_HOURS_PER_FARM_WORKER / REFERENCE_LABOUR_HOURS_PER_HECTARE
                               / (1.0 - FALLOW_SHARE_OF_HOLDING))


class Colonies:
    """Mixed into `Land`."""

    needs: Any
    seat: Any

    def settlement_spec(self, by_sea: bool = False) -> Optional[Tuple[str, Dict[str, Any]]]:
        """(node id, spec) of the best known `settlement` work that can make this voyage, or None: the one that
        sends the most settlers, ties by id."""
        done = self.needs.techniques_held()
        known = [(node_id, spec) for node_id, spec in self.needs.mechanic["settlement"].items() if node_id in done]
        return rules.best_settlement_work(known, by_sea)

    def settlement_candidates(self, by_sea: bool = False) -> List[str]:
        """Tiles a colony could be founded on now, best land first."""
        return settlement.candidate_tiles(self.home_tiles_held(), self.claimed_tiles(), by_sea)

    def settlement_outfit_cost(self, spec: Dict[str, Any], tile_id: Optional[str] = None) -> float:
        """What outfitting the settlers costs: a year's work for each at the society's wage, and more of them
        fitted out where the tile's diseases will take some before they are established."""
        return rules.outfit_cost(spec, self.needs.money_per_labour_hour(),
                                 self.needs.regional_disease_loss(tile_id) if tile_id else 0.0)

    def found_colony(self, command: FoundColony) -> Any:
        """Found a colony on the tile: {tile, settlers, cost, text}, or a Refusal naming why not."""
        tile_id = command.tile
        needs = self.needs
        by_land = tile_id in self.settlement_candidates(False)
        by_sea = tile_id in self.settlement_candidates(True)
        chosen = self.settlement_spec(by_sea=not by_land)
        node_id, spec = chosen if chosen else (None, None)
        settlers = float(spec["settlers"]) if spec else 0.0
        cost = self.settlement_outfit_cost(spec, tile_id) if spec else 0.0
        cause = rules.founding_refusal(self.tile_owner(tile_id) is not None, by_land, by_sea, chosen is not None,
                                       needs.working_age(), settlers, cost, needs.spending_power("buy"))
        if cause == "tile_held":
            return Refusal(cause, "that tile is already held")
        if cause == "unreachable":
            return Refusal(cause, "no settlers can reach that tile from what you hold; `settle` lists the tiles they can")
        if cause == "no_settlement_work":
            return Refusal(cause, "you know no way to send settlers%s" % ("" if by_land else " across the sea"))
        if cause == "too_few_people":
            return Refusal(cause, "the country has too few people of working age to spare %s settlers" % needs.plain_number(settlers))
        if cause == "cannot_afford":
            return Refusal(cause, "outfitting %s settlers costs %s, more than you can raise" % (
                needs.plain_number(settlers), needs.money_text(cost, grouped=True)))
        needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "outfitting a settlement"))
        needs.send(SendSettlers(settlers))
        self.hand_over(tile_id, self.clock.acting_seat, tile_owners.settlement_level(), "colony founded")
        self.seat.colonies.append({
            "tile": tile_id, "founded_year": needs.year(), "by": node_id,
            "children": 0.0, "working_age": settlers, "elderly": 0.0})
        needs.send(RecordEvent.of("colony_founded", "a colony of %s settlers is founded on %s, outfitted for %s"
                                  % (needs.plain_number(settlers), tile_id, needs.money_text(cost, grouped=True))))
        return {"tile": tile_id, "settlers": settlers, "cost": cost,
                "text": "founded a colony on %s with %s settlers for %s" % (
                    tile_id, needs.plain_number(settlers), needs.money_text(cost, grouped=True))}

    def colony_rows(self) -> List[Dict[str, Any]]:
        """What the `colonies` listing shows of each colony the acting seat holds."""
        rows = []
        for colony in self.seat.colonies:
            rows.append({"tile": colony["tile"], "founded_year": colony["founded_year"],
                         "people": round(rules.colony_people(colony)),
                         "most_the_land_feeds": round(settlement.capacity_kcal_per_day(colony["tile"])
                                                      / demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)})
        return rows

    def advance_colonies(self, command: Any) -> None:
        """One year for every seat's colonies: the people work the land they can hold and eat what it gives."""
        burden = self.needs.disease_burden()
        for seat_id in self.needs.seat_list()["joined"]:
            colonies = self.seat_of(seat_id).colonies
            for colony in list(colonies):
                tile = colony["tile"]
                if rules.advance_colony(
                        colony, lambda hands: settlement.worked_kcal_per_day(tile, hands * HOLDING_HECTARES_PER_WORKER),
                        demography.Population, burden):
                    colonies.remove(colony)
                    self.hand_over(colony["tile"], None, None, "colony died out")
                    if seat_id == self.clock.acting_seat:
                        needs = self.needs
                        needs.send(RecordEvent.in_year(command.year, "colony_died_out",
                                                       "the colony on %s has died out" % colony["tile"], tile=colony["tile"]))
