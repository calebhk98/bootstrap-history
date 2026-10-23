"""The year's stability phase: each state's grievances, hunger and liability burden become unrest on its tiles; where the
discontented, armed, would more likely than not beat the garrison they rise and fight it (the battle rule), and a won rising
takes the tile from the state or, at the seat, replaces the ruler. A disputed accession is settled the same way at the seat.

The rules are in `sim/agents/{unrest,revolt,authority,ruler}.py` and `sim/world/battle.py`; this reads the tiles, the
armies and the state's books and writes the result back. Owners are taken in id order, tiles in id order, so a year does
not depend on the order things were created in a save."""
from typing import Any, Dict, List, Optional

from sim.agents.api import authority, collection, revolt, ruler, tax_burden, unrest
from sim.agents.api import government_levers_land as land_levers
from sim.agents.api import government_levers_tax
from sim.world import battle, campaign_contest, military_logistics
from sim.world.army_record import Army

from . import world_events

RISINGS_KEPT = 20


class RevoltYearMixin:

    def stability_owners(self) -> List[str]:
        """The countries with a state to be risen against: the home country, then the others in id order."""
        home = str(self.civ["id"])
        return [home] + sorted(owner for owner in self.actors.state.countries if owner != home)

    def step_revolts(self) -> None:
        for owner in self.stability_owners():
            if self.owner_has_state(owner):
                self._stability_of(owner)

    # ---- readings of a state's year
    def _state_grievance(self, world: Any, record: Any) -> Optional[float]:
        """What the state took (taxes, levies) and owes beyond what it gave (the dole), over its taxpayers' income; None while no taxpayer income is visible."""
        income = sum(world.notice_over(scale) * income for scale, income in world.visible_taxpayers())
        if income <= 0.0:
            return None
        wage = float(world.pay_per_person_year("labourer"))
        hours = float(world.hours_per_person_year)
        levy = sum(record.corvee_hours.values()) / hours * wage if hours > 0.0 else 0.0
        taken = sum(record.revenue_by_form.values()) + levy
        given = max(0.0, record.need.get("dole", 0.0) - record.unfunded.get("dole", 0.0))
        owed = sum(record.unfunded.values())
        return unrest.grievance(taken, owed, given, income)

    def _faction_readings(self, owner: str, people: float):
        """(people-weighted grievance, members) of the organised interest groups of the owner."""
        home = str(self.civ["id"])
        groups = [group for group in self.actors.of_kind("interest_group") if group.organised()
                  and (group.record.country or home) == owner]
        pairs = [(group.record.members, group.record.grievance) for group in groups]
        return unrest.faction_grievance(pairs, people), sum(members for members, _ in pairs)

    def _garrison_on(self, owner: str, tile: str) -> Optional[Army]:
        """The owner's soldiers on a tile: its field armies there and the share of its free soldiers the tile's people bear."""
        field = sorted((Army.from_dict(record) for record in self.army_records().values()
                        if record["owner"] == owner and record["tile"] == tile and record["soldiers"] >= 1.0),
                       key=lambda army: army.army_id)
        garrison = self._garrison(owner, tile, {})
        side = field + ([garrison] if garrison.soldiers > 0.0 else [])
        return campaign_contest.combine(side) if side else None

    def _stability_of(self, owner: str) -> None:
        world = self.owner_world(owner)
        record = world.government().record
        year = int(self.state.scenario.year)
        people_by_tile = {tile: people for tile, people in sorted(world.collection_people_by_tile().items()) if people > 0.0}
        record.land_taken_by_tile = unrest.fade_memory(record.land_taken_by_tile)
        if not people_by_tile:
            return
        people = sum(people_by_tile.values())
        for tile, count in people_by_tile.items():
            record.registered_people[tile] = max(record.registered_people.get(tile, 0.0), count)
        state_grievance = self._state_grievance(world, record)
        faction_grievance, faction_members = self._faction_readings(owner, people)
        felt = faction_grievance
        if state_grievance is not None:
            if record.grievance_reference is None:
                record.grievance_reference = state_grievance
            felt += unrest.adapted(state_grievance, record.grievance_reference)
            record.grievance_reference = unrest.adapt(record.grievance_reference, state_grievance)
        rule = government_levers_tax.liability_rule(record)
        rate = tax_burden.harvest_share_taken(world)
        eaten = self.state.population.regional_eaten_over_need
        reference = self._reference_equipment(owner)
        seat = collection.seat_tile(people_by_tile)
        record.unrest_by_tile, record.hold_by_tile = {}, {}
        for tile, count in people_by_tile.items():
            burden = unrest.liability_burden(rule, rate, record.registered_people[tile], count)
            share = unrest.unrest(felt + record.land_taken_by_tile.get(tile, 0.0), unrest.hunger(eaten.get(tile)), burden)
            record.unrest_by_tile[tile] = share
            soldiers = unrest.rising_soldiers(count, share, unrest.organisation(faction_members, people))
            garrison = self._garrison_on(owner, tile)
            site = self.campaign_site(tile)
            terrain = battle.terrain_factor(site.ruggedness, self.tile_fortification(tile))
            against = 0.0 if garrison is None else campaign_contest.strength_of(garrison, reference, terrain)
            strength = unrest.rising_strength(soldiers, reference)
            record.hold_by_tile[tile] = authority.hold(against, strength)
            if unrest.rises(strength, against):
                self._rising(owner, world, record, tile, soldiers, strength, garrison, against, tile == seat, year, "unrest")
        if record.succession_challenger:
            self._disputed_accession(owner, world, record, seat, people_by_tile, faction_members, reference, year)

    # ---- a rising and what it changes
    def _rising(self, owner: str, world: Any, record: Any, tile: str, soldiers: float, strength: float,
                garrison: Optional[Army], garrison_strength: float, on_seat: bool, year: int, cause: str) -> str:
        draw = world.rng_for("revolt", tile, year).random()
        result = revolt.resolve(soldiers, strength, 0.0 if garrison is None else garrison.soldiers, garrison_strength, on_seat, draw)
        world_events.record(self, "revolt", actors=[owner], tiles=[tile], cause=cause, outcome=result.kind,
                            rising_win_probability=result.rising_win_probability, rising_lost=result.rising_lost,
                            garrison_lost=result.garrison_lost)
        record.risings = (record.risings + [{"year": year, "tile": tile, "kind": result.kind, "soldiers": round(soldiers)}])[-RISINGS_KEPT:]
        self.strike_from_force(owner, result.garrison_lost)
        if result.kind == revolt.TILE_LOST:
            self.transfer_tile(tile, None, cause="revolt")
        elif result.kind == revolt.RULER_REPLACED:
            record.ruler_age = ruler.opening_age()
            record.ruler_backer = "rising" if cause == "unrest" else record.succession_challenger
            record.accession_due = True
        return result.kind

    def _disputed_accession(self, owner: str, world: Any, record: Any, seat: Optional[str], people_by_tile: Dict[str, float],
                            faction_members: float, reference: float, year: int) -> None:
        """The runner-up faction takes arms at the seat against the garrison there, in proportion to its backing."""
        challenger = record.succession_challenger
        backing = world.faction_backing() if hasattr(world, "faction_backing") else {}
        total = sum(backing.values())
        if seat is None or challenger not in backing or total <= 0.0:
            record.succession_challenger = ""
            return
        soldiers = unrest.rising_soldiers(people_by_tile[seat], backing[challenger] / total)
        garrison = self._garrison_on(owner, seat)
        terrain = battle.terrain_factor(self.campaign_site(seat).ruggedness, self.tile_fortification(seat))
        against = 0.0 if garrison is None else campaign_contest.strength_of(garrison, reference, terrain)
        self._rising(owner, world, record, seat, soldiers, unrest.rising_strength(soldiers, reference), garrison, against,
                     True, year, "disputed_accession")
        record.succession_challenger = ""
