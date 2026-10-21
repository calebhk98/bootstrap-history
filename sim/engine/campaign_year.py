"""The year's campaign phase: every army marches on its order, eats from what it carries and the land, wears down,
and where it stands on another actor's tile it besieges and storms it; a tile won is held at the level the control
data names and rises with the years it is held.

The rules are in `sim/world/campaign_*.py` and `battle.py`; this reads the tiles, the routes and the owners and
writes the result back. Armies are taken in id order, so a year does not depend on the order they were raised in
a save."""
from typing import Any, Dict, List

from sim.agents.api import army_raising
from sim.geography.api import (endemic_people_loss, food_potential, layer_value, reach, route, settlement,
                               tile_owners, usable_modes)
from sim.world import campaign_contest, campaign_supply, military_logistics
from sim.world.army_record import Army

from . import world_events

RETREAT_NOTE = "withdrew"


class CampaignYearMixin:

    # ---- readings of a tile
    def campaign_site(self, tile: str) -> campaign_contest.Site:
        cache = self.__dict__.setdefault("_campaign_sites", {})
        if tile not in cache:
            cache[tile] = (float(food_potential(tile, world_map=self.world_map)["total_kcal_per_year"]),
                           float(endemic_people_loss([tile], self.world_map).get("working_age", 0.0)),
                           float(layer_value(tile, "ruggedness_index", self.world_map) or 0.0))
        food, disease, ruggedness = cache[tile]
        return campaign_contest.Site(tile, food, self.campaign_store()["drawn"].get(tile, 0.0), disease, ruggedness)

    def _draw_down(self, tile: str, kcal: float) -> None:
        drawn = self.campaign_store()["drawn"]
        drawn[tile] = drawn.get(tile, 0.0) + kcal

    def campaign_modes(self, owner: str) -> List[str]:
        if owner == str(self.civ["id"]):
            return list(usable_modes([self.held_and_running()], self.world_map))
        return list(self.owner_world(owner).collection_modes())

    def campaign_column(self, army: Army, modes: List[str]) -> tuple:
        """(kg of grain a day the army's column brings, tile it comes from): the nearest tile of the owner's within the
        column's reach that still has grain to take."""
        days_to = reach([army.tile], modes, campaign_supply.carriage_range_days(), self.state.economy.improvements,
                        world_map=self.world_map)
        for tile, days in sorted(days_to.items(), key=lambda item: (item[1], item[0])):
            if self.tile_owner(tile) != army.owner:
                continue
            site = self.campaign_site(tile)
            if campaign_supply.tile_stock_kg(site.food_kcal_per_year, site.drawn_kcal) > 0.0:
                return campaign_supply.carriage_kg_per_day(army.animals, days), tile
        return 0.0, None

    def _camp(self, army: Army, days: float, modes: List[str], pay_years: float, lost: Dict[str, float]) -> None:
        """Spend `days` on the army's tile: the column's grain, the land's, then losses."""
        site = self.campaign_site(army.tile)
        per_day, source = self.campaign_column(army, modes)
        before = site.drawn_kcal
        result = campaign_contest.camp(army, days, site, per_day, pay_years)
        self._draw_down(army.tile, site.drawn_kcal - before)
        if source is not None and result["taken_carriage_kg"] > 0.0:
            self._draw_down(source, campaign_supply.kcal_of(result["taken_carriage_kg"]))
        for cause in ("hunger", "disease", "desertion"):
            lost[army.owner] = lost.get(army.owner, 0.0) + result[cause]
            if result[cause] >= 1.0:
                army.log.append({"kind": cause, "tile": army.tile, "soldiers": round(result[cause])})

    def _pay_years(self, army: Army) -> float:
        world = self.owner_world(army.owner)
        record = world.government().record
        owed = army_raising.pay_owed_share(record.arrears.get("army", 0.0), self.owner_force(army.owner), army.soldiers)
        army.pay_owed = owed
        return army_raising.pay_owed_years(owed, army.soldiers, float(world.pay_per_person_year("soldier")))

    # ---- the phase
    def step_campaigns(self) -> None:
        store = self.campaign_store()
        store["drawn"] = {}
        if not store["armies"]:
            return
        armies = {army_id: Army.from_dict(record) for army_id, record in sorted(store["armies"].items())}
        for army in armies.values():
            army.log = []
        self._defend(armies)
        lost: Dict[str, float] = {}
        references = {}
        for army_id in sorted(armies):
            if army_id in armies:
                self._campaign_army(armies[army_id], armies, lost, references)
        survivors = {army_id: army for army_id, army in armies.items() if army.soldiers >= 1.0}
        store["armies"] = {army_id: army.to_dict() for army_id, army in sorted(survivors.items())}
        for owner, killed in sorted(lost.items()):
            self.strike_from_force(owner, killed)
        self._keep_within_force(sorted({army.owner for army in survivors.values()}))
        self._consolidate_conquests()

    def _keep_within_force(self, owners: List[str]) -> None:
        """An army is a slice of the state's force: when the state keeps fewer soldiers than its armies hold, the
        armies are stood down by the same share."""
        records = self.army_records()
        for owner in owners:
            fielded = sum(float(record["soldiers"]) for record in records.values() if record["owner"] == owner)
            force = self.owner_force(owner)
            if fielded > force + 1e-9:
                share = max(0.0, force) / fielded
                for record in records.values():
                    if record["owner"] == owner:
                        for key in ("soldiers", "food_kg", "animals", "pay_owed"):
                            record[key] *= share
        store = self.campaign_store()
        store["armies"] = {army_id: record for army_id, record in store["armies"].items() if record["soldiers"] >= 1.0}

    def _defend(self, armies: Dict[str, Army]) -> None:
        """A state no seat plays raises and orders armies to the tiles other owners' armies threaten."""
        played = {seat.country or str(self.civ["id"]) for seat in self.state.seats.values()
                  if getattr(seat, "kind", None) == "country"}
        owners = self.tile_owner_map()
        by_tile = {tile: entry["owner"] for tile, entry in owners.items()}
        records = {army_id: army.to_dict() for army_id, army in armies.items()}
        for owner in sorted(set(by_tile.values()) - played):
            if not self.owner_has_state(owner):
                continue   # a seat's colony: no state of its own to decide
            for tile, soldiers in army_raising.defence_musters(owner, by_tile, records, self.free_soldiers(owner)):
                made = self.raise_army(owner, soldiers, tile)
                if isinstance(made, Army):
                    armies[made.army_id], records[made.army_id] = made, made.to_dict()
            for army_id, tile in army_raising.defence_orders(owner, by_tile, records):
                armies[army_id].target, armies[army_id].progress_days = (
                    None if tile == armies[army_id].tile else tile), 0.0

    def _campaign_army(self, army: Army, armies: Dict[str, Army], lost: Dict[str, float], references: Dict) -> None:
        owner = army.owner
        reference = references.setdefault(owner, self._reference_equipment(owner))
        modes = self.campaign_modes(owner)
        pay_years = self._pay_years(army)
        days_left = campaign_supply.CAMPAIGN_SEASON_DAYS
        moved = False
        if army.target and army.target != army.tile:
            held = self.held_and_running()
            found = route([army.tile], [army.target], modes, self.state.economy.improvements, held_nodes=held,
                          world_map=self.world_map, fastest=True)
            if found is None:
                army.log.append({"kind": "no_route", "tile": army.tile, "target": army.target})
                army.target = None
            else:
                steps, army.progress_days, used = campaign_contest.march(
                    campaign_contest.legs_of(found), army.progress_days, days_left)
                for tile, days in steps:
                    army.tile = tile
                    self._camp(army, days, modes, pay_years, lost)
                if used > sum(days for _, days in steps):
                    self._camp(army, used - sum(days for _, days in steps), modes, pay_years, lost)
                days_left -= used
                moved = True
                if army.tile == army.target:
                    army.target, army.progress_days = None, 0.0
        occupier = self.tile_owner(army.tile)
        if occupier is not None and occupier != owner and army.soldiers >= 1.0:
            self._contest(army, armies, occupier, days_left, modes, pay_years, lost, reference)
        elif occupier != owner and days_left > 0.0 and army.soldiers >= 1.0:
            self._camp(army, days_left, modes, pay_years, lost)   # in the wild it lives off the land
        elif moved and army.soldiers >= 1.0:
            army.supply_state = 1.0                               # at home, its own state feeds it

    def _reference_equipment(self, owner: str) -> float:
        """The equipment burden of the reference soldier, whose quality is 1: the plain iron kit of the logistics model."""
        return military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()

    def _garrison(self, defender: str, tile: str, armies: Dict[str, Army]) -> Army:
        """The soldiers of the defending state not in an army, shared over its tiles by their people, as a force
        on the tile with the state's equipment and no food of its own: it eats the tile's stores."""
        owned = self.tiles_owned_by(defender)
        share = settlement.population_share(owned, tile) if tile in owned else 0.0
        free = self.free_soldiers(defender) * share
        equipment = float(self.owner_world(defender).equipment_kg_per_soldier()) if self.owner_has_state(defender) else 0.0
        return Army("garrison", defender, tile, free, equipment)

    def _contest(self, army: Army, armies: Dict[str, Army], defender: str, days_left: float, modes: List[str],
                 pay_years: float, lost: Dict[str, float], reference: float) -> None:
        tile = army.tile
        field = sorted((other for other in armies.values() if other.owner == defender and other.tile == tile
                        and other.soldiers >= 1.0), key=lambda other: other.army_id)
        garrison = self._garrison(defender, tile, armies)
        side = field + ([garrison] if garrison.soldiers >= 1.0 else [])
        rng = self.owner_world(army.owner).rng_for("battle", tile, army.army_id, int(self.state.scenario.year))
        site = self.campaign_site(tile)
        site.fortification = self.tile_fortification(tile)
        result = "defenders_gone" if not side else "continues"
        while side and days_left > 0.0:
            before = sum(member.soldiers for member in side)
            combined = campaign_contest.combine(side)
            turn_days = min(campaign_contest.SIEGE_TURN_DAYS, days_left)
            drawn_before = site.drawn_kcal
            per_day, source = self.campaign_column(army, modes)
            attacker_before = army.soldiers
            turn = campaign_contest.siege_turn(army, combined, site, per_day, reference, rng.random(), turn_days, pay_years)
            self._draw_down(tile, site.drawn_kcal - drawn_before)
            if source is not None and turn["carriage_taken_kg"] > 0.0:
                self._draw_down(source, campaign_supply.kcal_of(turn["carriage_taken_kg"]))
            campaign_contest.share_out(side, before, combined)
            lost[army.owner] = lost.get(army.owner, 0.0) + attacker_before - army.soldiers
            lost[defender] = lost.get(defender, 0.0) + before - sum(member.soldiers for member in side)
            days_left -= turn_days
            result = turn["result"]
            if turn["outcome"] is not None:
                world_events.record(self, "battle", actors=[army.owner, defender], tiles=[tile],
                                    cause="assault", attacker_won=turn["outcome"].attacker_won,
                                    attacker_win_probability=turn["outcome"].attacker_win_probability,
                                    attacker_lost=turn["outcome"].attacker_lost, defender_lost=turn["outcome"].defender_lost)
            if result != "continues":
                break
        if result in ("attacker_won", "defenders_gone"):
            self._take(army, defender, armies)
        elif result in ("attacker_lost", "attacker_withdraws"):
            self._withdraw(army, result)
        for member in side:
            if member is not garrison and member.soldiers < 1.0:
                armies.pop(member.army_id, None)
        if result in ("attacker_won", "defenders_gone"):
            for member in field:
                if member.army_id in armies:
                    self._rout(member, armies)

    def tile_fortification(self, tile: str) -> float:
        """The strength works add to a defender on this tile. No works the model reads yet add any."""
        return 0.0

    def _take(self, army: Army, defender: str, armies: Dict[str, Army]) -> None:
        """The army holds a tile whose defenders are gone: it passes to the army's owner at the level newly taken ground
        is held at, and the tile's people and taxes follow through the owner map."""
        tile = army.tile
        previous = self.transfer_tile(tile, army.owner, tile_owners.conquest_level(0.0), cause="conquest")
        self.campaign_store()["held_since"][tile] = {"year": int(self.state.scenario.year), "by": army.owner,
                                                      "from": previous}
        army.log.append({"kind": "conquest", "tile": tile, "from": previous})

    def _withdraw(self, army: Army, why: str) -> None:
        owned_home = army.home_tile and self.tile_owner(army.home_tile) == army.owner
        army.log.append({"kind": RETREAT_NOTE, "tile": army.tile, "why": why})
        army.target, army.progress_days = None, 0.0
        if owned_home:
            army.tile = army.home_tile

    def _rout(self, army: Army, armies: Dict[str, Army]) -> None:
        """A defending army beaten on its own ground falls back to the tile it was raised at, if that is still its
        owner's and not this one, else its men go home and it is stood down."""
        if army.home_tile and army.home_tile != army.tile and self.tile_owner(army.home_tile) == army.owner:
            army.tile, army.target, army.progress_days = army.home_tile, None, 0.0
        else:
            armies.pop(army.army_id, None)

    def _consolidate_conquests(self) -> None:
        """A tile taken by an army rises in control the longer its owner holds it with an army on it."""
        held_since = self.campaign_store()["held_since"]
        controls = self.stores.view("control")
        year = int(self.state.scenario.year)
        levels = tile_owners.control_levels()
        for tile, entry in sorted(held_since.items()):
            if self.tile_owner(tile) != entry["by"]:
                del held_since[tile]
                continue
            if any(record["owner"] == entry["by"] and record["tile"] == tile for record in self.army_records().values()):
                level = tile_owners.conquest_level(year - entry["year"])
                if levels[level]["rank"] > levels.get(controls.get(tile), {"rank": 0})["rank"]:
                    controls.set(tile, level)
