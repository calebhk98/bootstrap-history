"""The deposits a seat's mines name: which it has found, how much each can yield, what has been drawn, and prospecting.

A working names one deposit of the resource it raises. The deposits a seat can name are those geography lists for its held
tiles (the catalogue's known mines, first worked by now, and any hidden deposit its prospecting found). A deposit's size is
the catalogue's endowment; where the catalogue gives none, geography's expected size for the district stands in for it; a
row sized by the older output model keeps that model's output for the site over a working life; a deposit of unknown size
cannot be named. A deposit already worked before the game began has yielded its share of the size (`mined_before`); every
tonne the seat's workings, or the agent economy's firms on the tile, raise since is drawn from it. The most a deposit yields
in a year is a share of its size, or the rate the data say it was worked at when that is larger, less what other workings
named on it already rate, so a working's output is bounded by its deposit and a worked-out deposit closes it."""
from typing import Any, Dict, List, Optional, Tuple

from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.refusal import Refusal
from sim.world import deposits as deposit_model

from . import rules
from .commands import DrawDeposit, Prospect
from .constants import AUTO_PROSPECT_PERSON_DAYS, PROSPECT_HOURS_PER_PERSON_DAY
from .deposit_history import historical_rates

# Catalogue mechanisms that describe something dug out of the ground; a herd animal, a stand or a fishery sharing a good's
# name (cattle, cattle_kg) is no deposit.
DEPOSIT_MECHANISMS = ("mineral_deposit", "point_occurrence", "surface_stock")
NO_DEPOSIT_TEXT = ("you know of no deposit of %s with room on the tiles you hold; prospect for one "
                   "('prospect <tile> %s <person_days>')")


class Deposits:
    """Needs: deposit_catalogue, deposits_listed, deposits_worked_before, deposit_working_rate, prospect_finds, tile_endowment,
    tiles_listed_by, civilisation, year, start_year, labour_quote, weather_seed, purchase_budget, can_pay,
    afford_means, money_text, mass_text, mine_trade. Sends PayEdge."""

    def mine_resource_id(self, material: str) -> Optional[str]:
        """The catalogue resource a mine of `material` raises (the material's short name or its `_kg` key), or None for a
        material no deposit data describes."""
        mechanisms = self.needs.deposit_catalogue()["mechanisms"]
        for name in (material, str(material)[:-3] if str(material).endswith("_kg") else None):
            if name in mechanisms and mechanisms[name] in DEPOSIT_MECHANISMS:
                return name
        return None

    def modelled_sizes(self, resource_id: str) -> Dict[str, float]:
        """{deposit id: tonnes} from the older deposit model's yearly output over a working life, for a metal."""
        sizes = self._modelled_sizes
        if resource_id not in sizes:
            sizes[resource_id] = {} if resource_id not in self.needs.deposit_catalogue()["metals"] else {
                deposit.name: deposit.quantity_tonnes_per_year * deposit_model.DEPOSIT_ASSUMED_WORKING_LIFE_YEARS
                for deposit in deposit_model.load_deposits(resource_id)}
        return sizes[resource_id]

    def worked_before_start(self, resource_id: str, tiles: Tuple[str, ...]) -> Dict[str, float]:
        """{deposit id: share of its endowment worked out before the game began}."""
        mined = self.needs.deposits_worked_before(tiles, resource_id, int(self.needs.start_year()),
                                                  historical_rates(self.needs.deposit_catalogue()["metals"], resource_id))
        return {working["id"]: working["mined_share"] for working in mined["workings"]}

    def deposit_rows(self, resource_id: str, tiles: Tuple[str, ...], found: List[Dict[str, Any]], store_key: Any):
        """[(row, size in tonnes, share worked out before the game)] of the deposits on `tiles` (plus the prospected
        `found`), kept until the year, the tiles or the deposits found change."""
        year = self.needs.year()
        key = (tiles, year, len(found))
        cached = self._deposit_cache.get(store_key)
        if cached is None or cached[0] != key:
            modelled = self.modelled_sizes(resource_id)
            before = self.worked_before_start(resource_id, tiles)
            rows = []
            for row in self.needs.deposits_listed(tiles, resource_id, year, found):
                size = row["size_tonnes"] if row["size_tonnes"] is not None else modelled.get(row["id"])
                if size is not None:
                    rows.append((row, size, before.get(row["id"], 0.0)))
            cached = self._deposit_cache[store_key] = (key, rows)
        return cached[1]

    def deposit_base(self, resource_id: str):
        """The deposits this seat can name: its held tiles, and what prospecting found."""
        tiles = tuple(self.needs.tiles_listed_by(self.needs.civilisation()))
        return self.deposit_rows(resource_id, tiles, self.seat.deposits_found, resource_id)

    def priced_rows(self, resource_id: str, base) -> List[Dict[str, Any]]:
        drawn = self.seat.deposit_drawn
        history = historical_rates(self.needs.deposit_catalogue()["metals"], resource_id)
        return [rules.priced_row(row, size, before, drawn.get(row["id"], 0.0),
                                 self.needs.deposit_working_rate(size), history.get(row["id"], 0.0),
                                 rules.capacity_naming(self.seat.mines or (), self.seat.mine_tranches or (), row["id"]))
                for row, size, before in base]

    def empire_output(self) -> Dict[str, Any]:
        """The reference empire's yearly output of the tracked commodities, by commodity: {"t_per_yr": ...}."""
        return deposit_model.empire_output_100ad()

    def found_deposits(self, material: str) -> List[Dict[str, Any]]:
        """The deposits of `material` this seat can name, each {id, name, tile_id, size_tonnes, remaining_tonnes,
        grade_kg_per_tonne, rate_tonnes_per_year, room_tonnes_per_year}; empty for a material with no deposit data."""
        resource_id = self.mine_resource_id(material)
        if resource_id is None:
            return []
        return self.priced_rows(resource_id, self.deposit_base(resource_id))

    def partner_deposits(self, material: str, tile_ids) -> List[Dict[str, Any]]:
        """The catalogue deposits of `material`, first worked by now, on those of `tile_ids` the seat does not hold: the
        sites of the partner economies' own firms. The seat cannot name them; the firms working them draw them down."""
        resource_id = self.mine_resource_id(material)
        if resource_id is None:
            return []
        held = set(self.needs.tiles_listed_by(self.needs.civilisation()))
        tiles = tuple(sorted(set(tile_ids) - held))
        if not tiles:
            return []
        return self.priced_rows(resource_id, self.deposit_rows(resource_id, tiles, (), (resource_id, "partner")))

    def mine_room_in_deposits(self, material: str, deposit: Optional[str] = None) -> Optional[float]:
        """Tonnes a year of `material` the named deposit, else every found deposit, has room for; None where `material`
        has no deposit data, so nothing bounds the working but the ceiling."""
        if self.mine_resource_id(material) is None:
            return None
        return rules.room_in_deposits(self.found_deposits(material), deposit)

    def allocate_to_deposits(self, material: str, tonnes: float, deposit: Optional[str] = None) -> List[Tuple[Optional[str], float]]:
        """[(deposit id, tonnes a year)] naming where `tonnes` of new capacity goes; [(None, tonnes)] for a material with no
        deposit data."""
        if self.mine_resource_id(material) is None:
            return [(None, tonnes)]
        return rules.allocation_plan(self.found_deposits(material), tonnes, deposit)

    def deposit_remaining_tonnes(self, material: str, deposit_id: str) -> float:
        """What is left in a found deposit of `material`, in tonnes of the resource (0 for one not found)."""
        return next((row["remaining_tonnes"] for row in self.found_deposits(material) if row["id"] == deposit_id), 0.0)

    def draw_deposit(self, command: DrawDeposit) -> float:
        """Take `tonnes` of the resource from a deposit; answers what it could give."""
        return self.draw(command.deposit, command.tonnes)

    def draw(self, deposit_id: str, tonnes: float) -> float:
        drawn = self.seat.deposit_drawn
        drawn[deposit_id] = drawn.get(deposit_id, 0.0) + max(0.0, tonnes)
        return tonnes

    def prospect(self, command: Prospect) -> Any:
        """Prospect a held tile for a material with `person_days` of effort, paid at the mining trade's wage; the deposits
        found are kept."""
        tile_id, material, person_days = command.tile, command.material, command.person_days
        resource_id = self.mine_resource_id(material)
        if resource_id is None:
            return Refusal("no_deposit_data", "no deposit data describes %s; there is nothing to prospect for." % material,
                           material=material)
        if tile_id not in self.needs.tiles_listed_by(self.needs.civilisation()):
            return Refusal("not_held", "prospect only on a tile your nation holds.", tile=tile_id)
        if person_days <= 0:
            return Refusal("no_effort", "say how many person-days to spend prospecting.")
        hours = person_days * PROSPECT_HOURS_PER_PERSON_DAY
        cost = hours * self.needs.labour_quote(self.mine_trade(), hours)
        if not self.needs.can_pay(cost):
            return Refusal("cannot_afford", "prospecting %.0f person-days costs about %s; %s." % (
                person_days, self.needs.money_text(cost, True), self.needs.afford_means()), cost=cost)
        self.needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "prospecting"))
        seat = self.seat
        already = {row["id"] for row in seat.deposits_found}
        seed = self.needs.weather_seed(0, region="prospecting")   # the game's own dice, kept in the save
        key = "%s:%s" % (tile_id, resource_id)
        total = person_days + seat.prospected_person_days.get(key, 0.0)
        seat.prospected_person_days[key] = total
        new = [dict(found) for found in self.needs.prospect_finds(tile_id, resource_id, total, seed)
               if found["id"] not in already]
        seat.deposits_found.extend(new)
        if not new:
            return {"cost": cost, "found": [], "message": "spent %s on prospecting %s at %s and found nothing new." % (
                self.needs.money_text(cost, True), resource_id, tile_id)}
        sizes = {row["id"]: row["size_tonnes"] for row in self.found_deposits(material)}
        return {"cost": cost, "found": [found["id"] for found in new],
                "message": "spent %s prospecting %s at %s and found %d deposit(s): %s." % (
                    self.needs.money_text(cost, True), resource_id, tile_id, len(new),
                    ", ".join("%s (%s)" % (found["id"], self.needs.mass_text(sizes.get(found["id"]) or 0.0, short=True))
                              for found in new))}

    def auto_prospect(self, material: str) -> bool:
        """When the automatic mine finds no room in the deposits found for `material`, prospect the held tile expected to
        hold most of it undiscovered. Does nothing where a deposit has room or `material` has no deposit data."""
        resource_id = self.mine_resource_id(material)
        room = self.mine_room_in_deposits(material)
        if resource_id is None or room is None or room > 0.0:
            return False
        tiles = self.needs.tiles_listed_by(self.needs.civilisation())
        if not tiles:
            return False
        best = max(sorted(tiles), key=lambda tile: self.needs.tile_endowment(tile, resource_id)["undiscovered_expected"])
        return not isinstance(self.prospect(Prospect(best, material, AUTO_PROSPECT_PERSON_DAYS)), Refusal)
