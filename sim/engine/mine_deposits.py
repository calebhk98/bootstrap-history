"""The deposits a seat's mines name: which it has found, how much each can yield, and what has been drawn.

A working names one deposit of the resource it raises. The deposits a seat can name are those geography
lists for its held tiles (the catalogue's known mines, first worked by now, and any hidden deposit its
prospecting found: `state.holdings.deposits_found`). A deposit's size is the catalogue's endowment; where
the catalogue gives none, the older deposit model's output for the site over a working life stands in for
it [temporary_heuristic: DEPOSIT_ASSUMED_WORKING_LIFE_YEARS], and a deposit of unknown size cannot be named.
A deposit already worked before the game began has yielded its share of the endowment
(`mined_before`); every tonne the seat's workings, or the agent economy's firms on the tile, raise since is
drawn from it (`state.holdings.deposit_drawn`). The most a deposit yields in a year is a share of its size
(`resources_working_share_per_year`), less what other workings named on it already rate, so a working's
output is bounded by its deposit and a worked-out deposit closes it.

Methods of Sim, a mixin only so they live in a file of their own.
"""
from sim.constants import declare
from .units_prose import mass_text, money_text
import sim.geography.api as geography
from sim.world import deposits as deposit_model

NO_DEPOSIT_TEXT = ("you know of no deposit of %s with room on the tiles you hold; prospect for one "
                   "('prospect <tile> %s <person_days>')")


class MineDepositsMixin:

    def mine_resource_id(self, mat):
        """The catalogue resource a mine of `mat` raises (the material's short name or its `_kg` key), or None
        for a material no deposit data describes."""
        ids = geography.resource_ids(self.world_map)
        for name in (mat, str(mat)[:-3] if str(mat).endswith("_kg") else None):
            if name in ids and self.world_map.catalogue("resources")[name].get("mechanism") != "biotic_stand":
                return name
        return None

    def _modelled_sizes(self, resource_id):
        """{deposit id: tonnes} from the older deposit model's yearly output over a working life, for a metal."""
        if resource_id not in deposit_model.metals(self.world_map):
            return {}
        return {deposit.name: deposit.quantity_tonnes_per_year * deposit_model.DEPOSIT_ASSUMED_WORKING_LIFE_YEARS
                for deposit in deposit_model.load_deposits(resource_id)}

    def _worked_before_start(self, resource_id, tiles):
        """{deposit id: share of its endowment worked out before the game began}."""
        share = float(geography.parameter_value("resources_working_share_per_year", self.world_map))
        mined = geography.mined_before(tiles, resource_id, int(self.cfg["start_year"]), self.world_map)
        return {working["id"]: min(1.0, working["years_worked"] * share) for working in mined["workings"]}

    def _deposit_base(self, resource_id):
        """[(row, size in tonnes, share worked out before the game)] of the deposits this seat can name, kept
        until the year, the tiles or the deposits found change."""
        holdings = self.state.holdings
        tiles = tuple(geography.tiles_held(self.civ, self.world_map))
        found = holdings.deposits_found
        key = (resource_id, tiles, self.state.scenario.year, len(found))
        cached = self.__dict__.get("_deposit_base_cache")
        if cached is None or cached[0] != key:
            modelled = self._modelled_sizes(resource_id)
            before = self._worked_before_start(resource_id, tiles)
            rows = []
            for row in geography.worked_deposits(tiles, resource_id, self.state.scenario.year, found, self.world_map):
                size = row["size_tonnes"] if row["size_tonnes"] is not None else modelled.get(row["id"])
                if size is not None:
                    rows.append((row, size, before.get(row["id"], 0.0)))
            cached = self.__dict__["_deposit_base_cache"] = (key, rows)
        return cached[1]

    def found_deposits(self, mat):
        """The deposits of `mat` this seat can name, each {id, name, tile_id, size_tonnes, remaining_tonnes,
        grade_kg_per_tonne, rate_tonnes_per_year, room_tonnes_per_year}; empty for a material with no deposit data."""
        resource_id = self.mine_resource_id(mat)
        if resource_id is None:
            return []
        drawn = self.state.holdings.deposit_drawn
        rows = []
        for row, size, before in self._deposit_base(resource_id):
            remaining = max(0.0, size * (1.0 - before) - drawn.get(row["id"], 0.0))
            rate = min(geography.working_rate_tonnes_per_year(size, self.world_map), remaining)
            rows.append(dict(row, size_tonnes=size, remaining_tonnes=remaining, rate_tonnes_per_year=rate,
                             room_tonnes_per_year=max(0.0, rate - self._capacity_naming(row["id"]))))
        return rows

    def _capacity_naming(self, deposit_id):
        """Tonnes a year of workings, standing and being sunk, that name this deposit."""
        holdings = self.state.holdings
        standing = sum(working["capacity"] for working in holdings.mines or () if working.get("deposit") == deposit_id)
        sinking = sum(tranche[1] for tranche in holdings.mine_tranches or ()
                      if len(tranche) > 5 and tranche[5] == deposit_id)
        return standing + sinking

    def mine_room_in_deposits(self, mat, deposit=None):
        """Tonnes a year of `mat` the named deposit, else every found deposit, has room for; None where `mat`
        has no deposit data, so nothing bounds the working but the ceiling."""
        if self.mine_resource_id(mat) is None:
            return None
        return sum(row["room_tonnes_per_year"] for row in self.found_deposits(mat)
                   if deposit is None or row["id"] == deposit)

    def allocate_to_deposits(self, mat, tonnes, deposit=None):
        """[(deposit id, tonnes a year)] naming where `tonnes` of new capacity goes: the named deposit, else the
        found deposits with most room first. [(None, tonnes)] for a material with no deposit data."""
        if self.mine_resource_id(mat) is None:
            return [(None, tonnes)]
        rows = sorted((row for row in self.found_deposits(mat) if deposit is None or row["id"] == deposit),
                      key=lambda row: (-row["room_tonnes_per_year"], row["id"]))
        plan, left = [], tonnes
        for row in rows:
            take = min(left, row["room_tonnes_per_year"])
            if take > 0.0:
                plan.append((row["id"], take))
                left -= take
        return plan

    def draw_deposit(self, deposit_id, tonnes):
        """Take `tonnes` of the resource from a deposit; returns what it could give."""
        drawn = self.state.holdings.deposit_drawn
        drawn[deposit_id] = drawn.get(deposit_id, 0.0) + max(0.0, tonnes)
        return tonnes

    def deposit_remaining_tonnes(self, mat, deposit_id):
        """What is left in a found deposit of `mat`, in tonnes of the resource (0 for one not found)."""
        return next((row["remaining_tonnes"] for row in self.found_deposits(mat) if row["id"] == deposit_id), 0.0)

    PROSPECT_HOURS_PER_PERSON_DAY = declare(
        "PROSPECT_HOURS_PER_PERSON_DAY", 10.0, kind="temporary_heuristic",
        unit="hours of the mining trade per person-day of prospecting", source=None, confidence="D",
        why="Turns the effort geography's prospecting takes (person-days) into the hours the mining trade's "
            "wage is paid for; the length of a working day, which the construction data states as ten hours.")

    def prospect_deposits(self, tile_id, mat, person_days):
        """Prospect a held tile for `mat` with `person_days` of effort, paid at the mining trade's wage; the
        deposits found are kept. Returns (ok, message)."""
        resource_id = self.mine_resource_id(mat)
        if resource_id is None:
            return False, "no deposit data describes %s; there is nothing to prospect for." % mat
        if tile_id not in geography.tiles_held(self.civ, self.world_map):
            return False, "prospect only on a tile your nation holds."
        if person_days <= 0:
            return False, "say how many person-days to spend prospecting."
        hours = person_days * self.PROSPECT_HOURS_PER_PERSON_DAY
        cost = hours * self.labour.labour_market.quote(self.MINE_TRADE, hours)
        from . import purchase_rule
        if not purchase_rule.can_pay(self, cost):
            return False, "prospecting %.0f person-days costs about %s; %s." % (
                person_days, money_text(cost, self, grouped=True), purchase_rule.afford_means())
        from sim.agents.api import edges
        self.pay_edge(edges.EDGE_BUILDERS, cost, "prospecting")
        holdings = self.state.holdings
        already = {row["id"] for row in holdings.deposits_found}
        seed = self._farm_year_weather_seed(0, region="prospecting")   # the game's own dice, kept in the save
        total = person_days + holdings.prospected_person_days.get("%s:%s" % (tile_id, resource_id), 0.0)
        holdings.prospected_person_days["%s:%s" % (tile_id, resource_id)] = total
        new = [dict(found) for found in geography.prospect(tile_id, resource_id, total, seed, self.world_map)
               if found["id"] not in already]
        holdings.deposits_found.extend(new)
        if not new:
            return True, "spent %s on prospecting %s at %s and found nothing new." % (
                money_text(cost, self, grouped=True), resource_id, tile_id)
        sizes = {row["id"]: row["size_tonnes"] for row in self.found_deposits(mat)}
        return True, "spent %s prospecting %s at %s and found %d deposit(s): %s." % (
            money_text(cost, self, grouped=True), resource_id, tile_id, len(new),
            ", ".join("%s (%s)" % (found["id"], mass_text(sizes.get(found["id"]) or 0.0, self, short=True))
                      for found in new))

    AUTO_PROSPECT_PERSON_DAYS = declare(
        "AUTO_PROSPECT_PERSON_DAYS", 2000.0, kind="temporary_heuristic",
        unit="person-days per tile per automatic search",
        source=None, confidence="D",
        why="How much prospecting the automatic mine buys on the held tile with most undiscovered resource "
            "when the deposits found have no room for the material it is short of; a round figure, not "
            "derived from how long a survey party took.")

    def auto_prospect(self, mat):
        """When the automatic mine finds no room in the deposits found for `mat`, prospect the held tile that is
        expected to hold most of it undiscovered. Does nothing where a deposit has room or `mat` has no deposit data."""
        resource_id = self.mine_resource_id(mat)
        room = self.mine_room_in_deposits(mat)
        if resource_id is None or room is None or room > 0.0:
            return False
        tiles = geography.tiles_held(self.civ, self.world_map)
        if not tiles:
            return False
        best = max(sorted(tiles), key=lambda tile: geography.endowment(tile, resource_id, self.world_map)["undiscovered_expected"])
        return self.prospect_deposits(best, mat, self.AUTO_PROSPECT_PERSON_DAYS)[0]
