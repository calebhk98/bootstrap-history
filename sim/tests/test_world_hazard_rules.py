"""World hazards, famine and the yearly checks (Complaints 493 and 640): the hazards are called on the module over plain
views, the checks on a stand-in game built here from the strata, actors and tile owners they read. The `world_events` command and the
log's save are in test_world_events_command_and_save."""
QUICK_TOPIC = True

import types
from unittest import mock

from .bridge_send import attach_send
from .harness import check
from sim.agents.api import Business
from sim.agents.business_plant import Plant
from sim.demography.api import KillPeople
from sim.engine import invariants
from sim.engine.tile_ownership import TileOwnershipMixin
from sim.hazards import world_data
from sim.reporting.api import RecordEvent
from sim.tests import event_stand_in, hazards_host, module_harness

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
        view=lambda name: (lambda: [HOME, PARTNER]),
        playing_seats=lambda: ["first"], stores=types.SimpleNamespace(view=lambda name: controls), controls=controls,
        world_map=types.SimpleNamespace(tiles={"t1": {}, "t2": {}, "t3": {}}))
    event_stand_in.stood_in(sim)
    sim.tile_owner_map = lambda: sim.state.economy.tile_owners

    def shock(share):
        sim.population.total *= 1.0 - share
    sim._apply_population_mortality_shock = shock
    sim.transfer_tile = lambda *arguments, **keywords: TileOwnershipMixin.transfer_tile(sim, *arguments, **keywords)
    return attach_send(sim)


# ---- a hazard hits each country: a KillPeople command, and a line in every playing seat's log
def hazard_module(strata=(), partners=(PARTNER,)):
    by_country = {}
    for each in strata:
        by_country.setdefault(each.record.country, []).append({"members": each.record.members, "shortfall": each.record.shortfall})
    return hazards_host.build(
        partners_in_agent_economy=list(partners), civilisation={"id": HOME}, year=100, weather_seed=lambda salt, region=None: 7,
        seat_list={"joined": ["first"], "playing": ["first"]}, country_strata=lambda country: by_country.get(country, []),
        answers={KillPeople: lambda command: {"year": 100, "facts": {"died": 1000.0 * command.share}}})


flood = next(each for each in world_data.hazards() if each["kind"] == "flood")
module = hazard_module()
with mock.patch.object(world_data, "hazards", lambda: [dict(flood, annual_chance=1.0)]):
    module.step_world_hazards([])
sent = module_harness.sent(module)
killed = [command for command in sent if isinstance(command, KillPeople)]
check("a certain flood hits both countries, each by the hazard's share",
      [(command.country, command.share, command.kind) for command in killed]
      == [(HOME, flood["population_loss"], "flood"), (PARTNER, flood["population_loss"], "flood")], killed)
check("the hit carries the hazard's cause and its loss as a fact",
      all(command.cause == flood["cause"] and command.facts == {"population_loss": flood["population_loss"]} for command in killed))
lines = [command for command in sent if isinstance(command, RecordEvent)]
check("every playing seat's log carries a line per hit, naming the hazard and the country",
      [(line.seat, line.kind, line.facts["hazard"], line.facts["country"]) for line in lines]
      == [("first", "world_hazard", "flood", HOME), ("first", "world_hazard", "flood", PARTNER)], lines)

# ---- a famine
module = hazard_module(strata=[stratum(PARTNER, 600.0, 0.6, "a"), stratum(PARTNER, 400.0, 0.2, "b"), stratum(HOME, 500.0, 0.0)])
module.step_famine_watch([])
famine = module.world_events("famine", actor=PARTNER)
check("a country whose food is short has a famine record carrying the people-weighted shortfall",
      len(famine) == 1 and abs(famine[0]["facts"]["food_shortfall"] - 0.44) < 1e-9 and famine[0]["facts"]["people"] == 1000.0, famine)
check("a country with food has none", not module.world_events("famine", actor=HOME))
with mock.patch.object(world_data, "famine_food_shortfall", lambda: 0.5):
    quiet = hazard_module(strata=[stratum(PARTNER, 600.0, 0.6, "a"), stratum(PARTNER, 400.0, 0.2, "b")])
    quiet.step_famine_watch([])
check("a shortfall under the threshold writes none", not quiet.world_events("famine"))
empty = hazard_module(strata=[stratum(PARTNER, 0.0, 1.0)])
empty.step_famine_watch([])
check("a country with no people writes none", not empty.world_events("famine"))

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
