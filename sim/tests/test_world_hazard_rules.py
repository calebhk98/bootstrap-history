"""World hazards, transfers, famine and the yearly checks (Complaints 493 and 640): each rule is called on a stand-in game
built here from the strata, actors, tile owners and cohort shock it reads. The `world_events` command and the
log's save are in test_world_events_command_and_save."""
QUICK_TOPIC = True

import types
from unittest import mock

from .harness import check
from sim.agents.api import Business
from sim.agents.business_plant import Plant
from sim.engine import invariants, world_events, world_hazard_data, world_hazards
from sim.engine.tile_ownership import TileOwnershipMixin

HOME, PARTNER = "rome", "han"


class Controls(dict):
    """The `control` tile store: the level each owned tile is held at."""

    def set(self, tile_id, level):
        self[tile_id] = level


def stratum(country, members, food_shortfall=0.0, name="stratum"):
    record = types.SimpleNamespace(kind="stratum", country=country, members=members, shortfall={"food": food_shortfall},
                                   workforce={}, business=None, royalty_owed={})
    return types.SimpleNamespace(actor_id="%s_%s" % (country, name), record=record)


def game(strata=(), actors=(), owners=None, home_people=1000.0, colonies=None):
    controls = Controls({tile: "garrisoned" for tile in (owners or {})})
    everyone = list(strata) + list(actors)
    sim = types.SimpleNamespace(
        state=types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=100),
            economy=types.SimpleNamespace(world_events=[], tile_owners=owners if owners is not None else {}, market_book={}),
            seats={"first": types.SimpleNamespace(holdings=types.SimpleNamespace(colonies=colonies or []),
                                                  household=types.SimpleNamespace(log=[]))}),
        civ={"id": HOME}, events=True, population=types.SimpleNamespace(total=home_people),
        actors=types.SimpleNamespace(of_kind=lambda kind: [each for each in everyone if each.record.kind == kind],
                                     actors={each.actor_id: each for each in everyone},
                                     world_for=lambda actor, world: None),
        partners_in_agent_economy=lambda: [PARTNER], _farm_year_weather_seed=lambda salt: 7,
        playing_seats=lambda: ["first"], stores=types.SimpleNamespace(view=lambda name: controls), controls=controls,
        world_map=types.SimpleNamespace(tiles={"t1": {}, "t2": {}, "t3": {}}))
    sim.tile_owner_map = lambda: sim.state.economy.tile_owners

    def shock(share):
        sim.population.total *= 1.0 - share
    sim._apply_population_mortality_shock = shock
    sim.transfer_tile = lambda *arguments, **keywords: TileOwnershipMixin.transfer_tile(sim, *arguments, **keywords)
    return sim


def always(kind):
    entry = next(each for each in world_hazard_data.hazards() if each["kind"] == kind)
    return entry, mock.patch.object(world_hazard_data, "hazards", lambda: [dict(entry, annual_chance=1.0)])


# ---- a hazard hits a partner by its strata, the home society by its cohort shock
flood, certain = always("flood")
sim = game(strata=[stratum(PARTNER, 600.0, name="a"), stratum(PARTNER, 400.0, name="b")])
with certain:
    world_hazards.world_hazards_phase(sim, [])
hits = world_events.rows(sim, "flood")
check("a certain flood hits both countries and writes one record each",
      sorted(row["actors"][0] for row in hits) == [PARTNER, HOME], hits)
partner_hit = next(row for row in hits if row["actors"] == [PARTNER])
check("the partner's strata fall by the hazard's share",
      abs(world_hazards.people_of(sim, PARTNER) - 1000.0 * (1 - flood["population_loss"])) < 1e-9, world_hazards.people_of(sim, PARTNER))
check("...and the record's death count is the people lost",
      abs(partner_hit["facts"]["died"] - 1000.0 * flood["population_loss"]) < 1e-9, partner_hit)
check("the home society falls by the same share through its cohorts",
      abs(sim.population.total - 1000.0 * (1 - flood["population_loss"])) < 1e-9, sim.population.total)
check("the record carries a year, a cause and structured facts",
      partner_hit["year"] == 100 and partner_hit["cause"] == flood["cause"] and partner_hit["facts"]["population_loss"] > 0)
seat_log = sim.state.seats["first"].household.log
check("every playing seat's log carries a line per hit, naming the hazard and the country",
      sorted((line.kind, line.facts["hazard"], line.facts["country"]) for _year, line in seat_log)
      == [("world_hazard", "flood", PARTNER), ("world_hazard", "flood", HOME)], seat_log)

# ---- a transfer writes a dated event
sim = game(owners={"t1": {"owner": HOME}, "t2": {"owner": HOME}})
previous = sim.transfer_tile("t1", PARTNER, "garrisoned", cause="conquest")
transfers = world_events.rows(sim, "tile_transfer")
check("a transfer returns the previous owner and moves the tile", previous == HOME and sim.state.economy.tile_owners["t1"] == {"owner": PARTNER})
check("it writes year, actors, tile, cause and facts",
      len(transfers) == 1 and transfers[0]["year"] == 100 and transfers[0]["tiles"] == ["t1"]
      and transfers[0]["cause"] == "conquest" and transfers[0]["actors"] == [HOME, PARTNER]
      and transfers[0]["facts"] == {"from_owner": HOME, "to_owner": PARTNER, "control": "garrisoned"}, transfers)
sim.transfer_tile("t2", None, cause="abandoned")
check("releasing a tile names only the previous owner", world_events.rows(sim, "tile_transfer")[-1]["actors"] == [HOME])

# ---- a famine
sim = game(strata=[stratum(PARTNER, 600.0, 0.6, "a"), stratum(PARTNER, 400.0, 0.2, "b"), stratum(HOME, 500.0, 0.0)])
world_hazards.famine_watch_phase(sim, [])
famine = world_events.rows(sim, "famine", actor=PARTNER)
check("a country whose food is short has a famine record carrying the people-weighted shortfall",
      len(famine) == 1 and abs(famine[0]["facts"]["food_shortfall"] - 0.44) < 1e-9 and famine[0]["facts"]["people"] == 1000.0, famine)
check("a country with food has none", not world_events.rows(sim, "famine", actor=HOME))
with mock.patch.object(world_hazard_data, "famine_food_shortfall", lambda: 0.5):
    quiet = game(strata=[stratum(PARTNER, 600.0, 0.6, "a"), stratum(PARTNER, 400.0, 0.2, "b")])
    world_hazards.famine_watch_phase(quiet, [])
check("a shortfall under the threshold writes none", not world_events.rows(quiet, "famine"))
check("a country with no people writes none", not world_events.rows(
    (lambda empty: (world_hazards.famine_watch_phase(empty, []), empty)[1])(game(strata=[stratum(PARTNER, 0.0, 1.0)])), "famine"))

# ---- the yearly checks each fail on a forced violation
def fails(check_function, target):
    try:
        check_function(target)
        return False
    except AssertionError:
        return True


def tiled():
    return game(owners={"t1": {"owner": "first"}, "t2": {"owner": PARTNER}}, colonies=[{"tile": "t1"}])


check("the ownership check holds on well-formed owners", invariants.check_tile_owner_invariants(tiled()) is True)
bad_level = tiled()
bad_level.controls["t1"] = "no_such_level"
check("the ownership check fails on an unknown control level", fails(invariants.check_tile_owner_invariants, bad_level))
off_map = tiled()
off_map.state.economy.tile_owners["elsewhere"] = {"owner": HOME}
off_map.controls["elsewhere"] = "garrisoned"
check("...on a tile the map lacks", fails(invariants.check_tile_owner_invariants, off_map))
rival = tiled()
rival.state.seats["second"] = types.SimpleNamespace(holdings=types.SimpleNamespace(colonies=[{"tile": "t1"}]))
check("...and on a tile two seats both list", fails(invariants.check_tile_owner_invariants, rival))


def running(technique, held):
    actor = types.SimpleNamespace(actor_id="church", record=types.SimpleNamespace(
        kind="church", country=HOME, business=Business.running([technique], opened_year=100), royalty_owed={}, workforce={}),
        knows=lambda entry_key, scope: entry_key in held)
    return game(actors=[actor])


check("the technique check holds when the actor holds what it runs",
      invariants.check_technique_invariants(running("iron_smelting", {"iron_smelting"})) is True)
check("the technique check fails when an actor runs a plant it does not hold",
      fails(invariants.check_technique_invariants, running("iron_smelting", set())))


def employing(staff, plant_size=1.0, crew_found=1.0):
    church = types.SimpleNamespace(actor_id="church", record=types.SimpleNamespace(
        kind="church", country=PARTNER, royalty_owed={}, workforce={"any_trade": staff},
        business=Business(plants=[Plant(entry_key="iron_smelting", size=plant_size, crew_found=crew_found)])))
    return game(strata=[stratum(PARTNER, 1000.0)], actors=[church])


check("the capacity check holds when an actor employs fewer people than the country has",
      invariants.check_capacity_invariants(employing(10.0)) is True)
check("the capacity check fails when an actor employs more people than the country has",
      fails(invariants.check_capacity_invariants, employing(1.0e15)))
check("...when a plant's size is negative", fails(invariants.check_capacity_invariants, employing(1.0, plant_size=-1.0)))
check("...when the share of its crew found is above one", fails(invariants.check_capacity_invariants, employing(1.0, crew_found=1.5)))
