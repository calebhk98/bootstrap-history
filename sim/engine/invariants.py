"""Pure, opt-in validation of state produced by one simulation turn."""
import math

VALID_PROJECT_STATUSES = frozenset(("ACTIVE", "PAUSED", "BLOCKED", "BLOCKED_INPUTS"))


def check_simulation_invariants(state):
    """Assert cross-subsystem rules without repairing or consulting globals."""
    people = state.modules["demography"]
    demographics = {
        "children": people.pop_children,
        "working_age": people.pop_working_age,
        "elderly": people.pop_elderly,
    }
    for key, value in demographics.items():
        assert math.isfinite(value) and value >= 0.0, \
            "invalid demographic %s=%r" % (key, value)
    for key, value in (state.seats[state.acting_seat].modules["ledger"].material_stock_ledger or {}).items():
        assert math.isfinite(value) and value >= -1e-9, \
            "negative or non-finite physical stockpile %s=%r" % (key, value)
    allocated_fte = 0.0
    for project_id, project in state.seats[state.acting_seat].modules["projects"].active.items():
        status = project.get("status")
        assert status in VALID_PROJECT_STATUSES, \
            "active project %s has invalid status %r" % (project_id, status)
        for field in ("hours_offered_this_year", "hours_directed_this_year",
                      "hours_effective_this_year"):
            value = project.get(field)
            if value is not None:
                assert math.isfinite(value) and value >= -1e-9, \
                    "active project %s has invalid %s=%r" % (project_id, field, value)
        allocated_fte += max(0.0, project.get("hours_effective_this_year") or 0.0) / 2000.0
        for trade, value in (project.get("lab_left") or {}).items():
            assert math.isfinite(value) and value >= -1e-9, \
                "active project %s has invalid assigned %s labor=%r" % (project_id, trade, value)
    assert allocated_fte <= demographics["working_age"] + 1e-6, \
        "allocated project labor %.3f FTE exceeds working population %.3f" % (
            allocated_fte, demographics["working_age"])
    return True


def check_tile_owner_invariants(sim):
    """Assert every tile has at most one owner: the owner map is well formed, and the tiles each seat's colonies
    stand on are listed by one seat only and owned by it."""
    found = sim.view("tile_ownership_problems")()
    assert not found, "tile ownership broken: %r" % (found,)
    return True


def check_price_invariants(sim):
    """Assert every price the agent economy quotes is finite and not negative (a good with no price is absent or None)."""
    for good, price in (sim.view("agent_prices")() or {}).items():
        assert price is None or (math.isfinite(price) and price >= 0.0), \
            "negative or non-finite commodity price %s=%r" % (good, price)
    return True


def check_labour_market_invariants(sim):
    """Assert the labour market never holds more people than exist."""
    nation = sim.view("population")().total
    town = sim.view("home_town_population_estimate")()
    assert town <= nation + 1e-6, \
        "home town of %.1f people exceeds the nation of %.1f" % (town, nation)
    employees = sim.view("staff")()["employees"]
    for trade in sim.view("available_trades")():
        reachable = sim.view("reachable_trade_population")[trade]
        people = sim.view("people_who_exist")[trade]
        assert reachable <= people + 1e-6, \
            "reachable %s %.2f exceed the %.2f people in that trade" % (trade, reachable, people)
        assert reachable <= nation + 1e-6, \
            "reachable %s %.2f exceed the nation of %.1f" % (trade, reachable, nation)
    staffed = sum(employees.values())
    available = sim.view("population")().working_age
    assert staffed <= available + 1e-6, \
        "%.1f staff on the payroll exceed the %.1f people of working age" % (staffed, available)
    return True


def check_technique_invariants(sim):
    """Assert no actor runs a plant of a technique it does not hold (its own knowledge, its country's baseline,
    or a licence it pays royalty under)."""
    registry = sim.view("cast")()
    world = sim.view("actor_world")()
    for actor in registry.actors.values():
        business = actor.record.business
        scope = registry.countries.world_for(actor, world)
        for entry_key in business.reading.entry_keys():
            held = actor.knows(entry_key, scope) or entry_key in actor.record.royalty_owed
            assert held, "%s runs %s without holding the technique" % (actor.actor_id, entry_key)
    return True


def check_capacity_invariants(sim):
    """Assert counts stay within production limits: a plant's size is finite and not negative, the share of its
    crew found lies in 0..1, no actor's workforce is negative or larger than the people of its country."""
    from .mod_effects import people_of
    registry = sim.view("cast")()
    people = {country: people_of(sim, country) for country in sim.view("countries_in_game")()}
    home = sim.civ["id"]
    for actor in registry.actors.values():
        business = actor.record.business
        for plant in business.plants:
            assert math.isfinite(plant.size) and plant.size >= 0.0, \
                "%s plant %s has size %r" % (actor.actor_id, plant.entry_key, plant.size)
            assert 0.0 <= plant.crew_found <= 1.0 + 1e-9, \
                "%s plant %s has crew found %r" % (actor.actor_id, plant.entry_key, plant.crew_found)
        staff = sum(actor.record.workforce.values())
        country = actor.record.country or home
        assert math.isfinite(staff) and staff >= -1e-9, "%s workforce %r" % (actor.actor_id, staff)
        if country in people and people[country] > 0.0:
            assert staff <= people[country] + 1e-6, \
                "%s employs %.1f, more than the %.1f people of %s" % (actor.actor_id, staff, people[country], country)
    return True


def check_yearly_invariants(sim):
    """The checks every year runs in a game of several countries, whether or not `sim.debug` is set: tile
    ownership, techniques held, and production limits."""
    check_tile_owner_invariants(sim)
    check_technique_invariants(sim)
    check_price_invariants(sim)
    return check_capacity_invariants(sim)
