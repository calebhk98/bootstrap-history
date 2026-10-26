"""Settled colonies: tiles a seat holds beyond its country's own, each with a people of its own.

A work declares `mechanics.settlement = {"settlers": n, "outfit_hours_per_settler": h, "by_sea": bool}`. Once a seat
knows one, it can found a colony on a tile that borders what it holds (or, by sea, a coastal tile when it holds a coastal
one): the settlers leave the home country's working age and the outfit is paid at the society's wage. The colony's people
are three age cohorts stepped each year by the same demography as the home country's (`sim/world/demography.py`),
fed by the tile's land in the share its working-age people can hold, as many hectares each as a farm worker holds at
home. A colony whose people die out is lost.
"""
from sim.agents.api import edges
from sim.demography.api import SendSettlers
from sim.geography.api import settlement, tile_owners

from sim.world.shared_constants import (
    ANNUAL_LABOUR_HOURS_PER_FARM_WORKER, FALLOW_SHARE_OF_HOLDING)
from sim.world.farm_labour import REFERENCE_LABOUR_HOURS_PER_HECTARE

from .colony_rules import advance_colony, best_settlement_work, colony_people, founding_refusal, outfit_cost
from .units_prose import money_text, plain_number
from sim.reporting.api import RecordEvent

# land one farm worker holds, fallow included: the hours a worker gives a year over the hours a cropped hectare takes
HOLDING_HECTARES_PER_WORKER = (ANNUAL_LABOUR_HOURS_PER_FARM_WORKER / REFERENCE_LABOUR_HOURS_PER_HECTARE
                               / (1.0 - FALLOW_SHARE_OF_HOLDING))


class ColoniesMixin:

    def settlement_spec(self, by_sea=False):
        """(node id, spec) of the best known `settlement` work that can make this voyage, or None: the one that
        sends the most settlers, ties by id."""
        known = [(node_id, self.mechanic(node_id, "settlement")) for node_id in self.nodes_with_mechanic("settlement")
                 if node_id in self.state.projects.done]
        return best_settlement_work(known, by_sea)

    def claimed_tiles(self):
        """Tiles some other actor owns (a seat's colony, a partner's land): a tile has one owner."""
        home = self.civ["id"]
        return [tile for tile, entry in self.tile_owner_map().items() if entry["owner"] != home]

    def settlement_candidates(self, by_sea=False):
        """Tiles a colony could be founded on now, best land first."""
        return settlement.candidate_tiles(self.home_tiles_held(), self.claimed_tiles(), by_sea)

    def settlement_outfit_cost(self, spec, tile_id=None):
        """What outfitting the settlers costs: a year's work for each at the society's wage, and more of them
        fitted out where the tile's diseases (`regional_disease_loss`) will take some before they are established."""
        return outfit_cost(spec, self.labour.money_per_labour_hour(),
                           self.regional_disease_loss(tile_id) if tile_id else 0.0)

    def found_colony(self, tile_id):
        """(ok, text): found a colony on `tile_id`."""
        household = self.state.household
        by_land = tile_id in self.settlement_candidates(False)
        by_sea = tile_id in self.settlement_candidates(True)
        chosen = self.settlement_spec(by_sea=not by_land)
        node_id, spec = chosen if chosen else (None, None)
        settlers = float(spec["settlers"]) if spec else 0.0
        cost = self.settlement_outfit_cost(spec, tile_id) if spec else 0.0
        cause = founding_refusal(self.tile_owner(tile_id) is not None, by_land, by_sea, chosen is not None,
                                 self.population.working_age, settlers, cost, self.spending_power("buy"))
        if cause == "tile_held":
            return False, "that tile is already held"
        if cause == "unreachable":
            return False, "no settlers can reach that tile from what you hold; `settle` lists the tiles they can"
        if cause == "no_settlement_work":
            return False, "you know no way to send settlers%s" % ("" if by_land else " across the sea")
        if cause == "too_few_people":
            return False, "the country has too few people of working age to spare %s settlers" % plain_number(settlers)
        if cause == "cannot_afford":
            return False, "outfitting %s settlers costs %s, more than you can raise" % (
                plain_number(settlers), money_text(cost, self, grouped=True))
        self.pay_edge(edges.EDGE_BUILDERS, cost, "outfitting a settlement")
        self.send(SendSettlers(settlers))
        self.transfer_tile(tile_id, self.state.acting_seat, tile_owners.settlement_level(), "colony founded")
        self.state.holdings.colonies.append({
            "tile": tile_id, "founded_year": self.state.scenario.year, "by": node_id,
            "children": 0.0, "working_age": settlers, "elderly": 0.0})
        self.send(RecordEvent.of("colony_founded", "a colony of %s settlers is founded on %s, outfitted for %s"
                              % (plain_number(settlers), tile_id, money_text(cost, self, grouped=True))))
        return True, "founded a colony on %s with %s settlers for %s" % (
            tile_id, plain_number(settlers), money_text(cost, self, grouped=True))

    def colony_rows(self):
        """What the `colonies` listing shows of each colony the acting seat holds."""
        rows = []
        for colony in self.state.holdings.colonies:
            rows.append({"tile": colony["tile"], "founded_year": colony["founded_year"], "people": round(colony_people(colony)),
                         "most_the_land_feeds": round(settlement.capacity_kcal_per_day(colony["tile"])
                                                      / self._demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)})
        return rows

    def advance_colonies(self, year):
        """One year for every seat's colonies: the people work the land they can hold and eat what it gives."""
        burden = self._disease_burden()
        for seat_id, seat in self.state.seats.items():
            for colony in list(seat.holdings.colonies):
                tile = colony["tile"]
                if advance_colony(colony, lambda hands: settlement.worked_kcal_per_day(tile, hands * HOLDING_HECTARES_PER_WORKER),
                                  self._demography.Population, burden):
                    seat.holdings.colonies.remove(colony)
                    self.transfer_tile(colony["tile"], None, cause="colony died out")
                    if seat_id == self.state.acting_seat:
                        self.send(RecordEvent.in_year(year, "colony_died_out", "the colony on %s has died out" % colony["tile"], tile=colony["tile"]))
