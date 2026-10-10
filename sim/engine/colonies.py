"""Settled colonies: tiles a seat holds beyond its country's own, each with a people of its own.

A work declares `mechanics.settlement = {"settlers": n, "outfit_hours_per_settler": h, "by_sea": bool}`. Once a seat
knows one, it can found a colony on a tile that borders what it holds (or, by sea, a coastal tile when it holds a coastal
one): the settlers leave the home country's working age and the outfit is paid at the society's wage. The colony's people
are three age cohorts stepped each year by the same demography as the home country's (`sim/world/demography.py`),
fed by the tile's land but only as far as the settlers' own hands, at the home country's output per worker, can work it.
A colony whose people die out is lost.
"""
from sim.agents.api import edges
from sim.geography.api import settlement, tiles_held

from .units_prose import money_text, plain_number

DAYS_PER_YEAR = 365.0


class ColoniesMixin:

    def settlement_spec(self, by_sea=False):
        """(node id, spec) of the best known `settlement` work that can make this voyage, or None: the one that
        sends the most settlers, ties by id."""
        known = [(node_id, self.mechanic(node_id, "settlement")) for node_id in self.nodes_with_mechanic("settlement")
                 if node_id in self.state.projects.done]
        fit = [(node_id, spec) for node_id, spec in known if spec.get("by_sea") or not by_sea]
        return max(fit, key=lambda item: (item[1]["settlers"], item[0]), default=None)

    def claimed_tiles(self):
        """Tiles the acting seat's colonies stand on."""
        return [colony["tile"] for colony in self.state.holdings.colonies]

    def settlement_candidates(self, by_sea=False):
        """Tiles a colony could be founded on now, best land first."""
        return settlement.candidate_tiles(list(tiles_held(self.civ)), self.claimed_tiles(), by_sea)

    def settlement_outfit_cost(self, spec):
        """What outfitting the settlers costs: a year's work for each at the society's wage."""
        return spec["settlers"] * spec["outfit_hours_per_settler"] * self.labour.money_per_labour_hour()

    def found_colony(self, tile_id):
        """(ok, text): found a colony on `tile_id`."""
        household = self.state.household
        if tile_id in self.claimed_tiles() or tile_id in tiles_held(self.civ):
            return False, "that tile is already held"
        by_land = tile_id in self.settlement_candidates(False)
        if not by_land and tile_id not in self.settlement_candidates(True):
            return False, "no settlers can reach that tile from what you hold; `settle` lists the tiles they can"
        chosen = self.settlement_spec(by_sea=not by_land)
        if chosen is None:
            return False, ("you know no way to send settlers%s" % ("" if by_land else " across the sea"))
        node_id, spec = chosen
        settlers = float(spec["settlers"])
        if self.population.working_age < 10.0 * settlers:
            return False, "the country has too few people of working age to spare %s settlers" % plain_number(settlers)
        cost = self.settlement_outfit_cost(spec)
        if cost > self.spending_power("buy"):
            return False, "outfitting %s settlers costs %s, more than you can raise" % (
                plain_number(settlers), money_text(cost, self, grouped=True))
        self.pay_edge(edges.EDGE_BUILDERS, cost, "outfitting a settlement")
        self.population.working_age -= settlers
        self.state.holdings.colonies.append({
            "tile": tile_id, "founded_year": self.state.scenario.year, "by": node_id,
            "children": 0.0, "working_age": settlers, "elderly": 0.0})
        household.log.append((self.state.scenario.year, "a colony of %s settlers is founded on %s, outfitted for %s"
                              % (plain_number(settlers), tile_id, money_text(cost, self, grouped=True))))
        return True, "founded a colony on %s with %s settlers for %s" % (
            tile_id, plain_number(settlers), money_text(cost, self, grouped=True))

    def colony_rows(self):
        """What the `colonies` listing shows of each colony the acting seat holds."""
        rows = []
        for colony in self.state.holdings.colonies:
            people = colony["children"] + colony["working_age"] + colony["elderly"]
            rows.append({"tile": colony["tile"], "founded_year": colony["founded_year"], "people": round(people),
                         "most_the_land_feeds": round(settlement.capacity_kcal_per_day(colony["tile"])
                                                      / self._demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)})
        return rows

    def advance_colonies(self, year, food_eaten_kcal_per_day):
        """One year for every seat's colonies. The settlers feed themselves from the tile at the home country's food
        per working-age person, never beyond what the land gives."""
        per_worker = food_eaten_kcal_per_day / max(1.0, self.population.working_age)
        burden = self._disease_burden()
        for seat_id, seat in self.state.seats.items():
            for colony in list(seat.holdings.colonies):
                people = self._demography.Population(colony["children"], colony["working_age"], colony["elderly"])
                food = min(settlement.capacity_kcal_per_day(colony["tile"]), people.working_age * per_worker)
                people.step(food, jitter=False, disease_burden=burden)
                colony.update(children=people.children, working_age=people.working_age, elderly=people.elderly)
                if people.total < 1.0:
                    seat.holdings.colonies.remove(colony)
                    if seat_id == self.state.acting_seat:
                        self.state.household.log.append((year, "the colony on %s has died out" % colony["tile"]))
