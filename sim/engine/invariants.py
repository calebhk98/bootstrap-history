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
    economy = state.economy
    holdings = state.holdings
    for key, value in (holdings._material_stock_ledger or {}).items():
        assert math.isfinite(value) and value >= -1e-9, \
            "negative or non-finite physical stockpile %s=%r" % (key, value)
    granary_kg = state.seats[state.acting_seat].modules["demography"].farm_stock_kg
    assert math.isfinite(granary_kg) and granary_kg >= -1e-9, \
        "negative or non-finite physical stockpile grain=%r" % granary_kg
    for key, value in (getattr(economy, "commodity_prices", None) or {}).items():
        assert math.isfinite(value) and value >= 0.0, \
            "negative or non-finite commodity price %s=%r" % (key, value)
    allocated_fte = 0.0
    for project_id, project in state.projects.active.items():
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


def check_labour_market_invariants(sim):
    """Assert the labour market never holds more people than exist."""
    nation = sim.population.total
    town = sim.labour.home_town_population_estimate()
    assert town <= nation + 1e-6, \
        "home town of %.1f people exceeds the nation of %.1f" % (town, nation)
    employees = sim.view("staff")()["employees"]
    for trade in sim.labour.available_trades():
        reachable = sim.labour.reachable_trade_population(trade)
        people = sim.labour.people_who_exist(trade)
        assert reachable <= people + 1e-6, \
            "reachable %s %.2f exceed the %.2f people in that trade" % (trade, reachable, people)
        assert reachable <= nation + 1e-6, \
            "reachable %s %.2f exceed the nation of %.1f" % (trade, reachable, nation)
    staffed = sum(employees.values())
    available = sim.population.working_age
    assert staffed <= available + 1e-6, \
        "%.1f staff on the payroll exceed the %.1f people of working age" % (staffed, available)
    return True


def check_technique_invariants(sim):
    """Assert no actor runs a plant of a technique it does not hold (its own knowledge, its country's baseline,
    or a licence it pays royalty under)."""
    registry = sim.actors
    world = sim.view("actor_world")()
    for actor in registry.actors.values():
        business = getattr(actor.record, "business", None)
        if business is None:
            continue
        scope = registry.world_for(actor, world)
        for entry_key in business.entry_keys():
            held = actor.knows(entry_key, scope) or entry_key in actor.record.royalty_owed
            assert held, "%s runs %s without holding the technique" % (actor.actor_id, entry_key)
    return True


def check_capacity_invariants(sim):
    """Assert counts stay within production limits: a plant's size is finite and not negative, the share of its
    crew found lies in 0..1, no actor's workforce is negative or larger than the people of its country, and each
    commodity's society capacity is finite and not negative."""
    from .mod_effects import people_of
    registry = sim.actors
    people = {country: people_of(sim, country) for country in sim.view("countries_in_game")()}
    home = sim.civ["id"]
    for actor in registry.actors.values():
        business = getattr(actor.record, "business", None)
        for plant in (business.plants if business is not None else ()):
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
    for commodity, book in (sim.state.modules["markets"].market_book or {}).items():
        capacity = book.get("capacity_tonnes", 0.0)
        assert math.isfinite(capacity) and capacity >= -1e-9, "commodity %s has capacity %r" % (commodity, capacity)
    return True


def check_yearly_invariants(sim):
    """The checks every year runs in a game of several countries, whether or not `sim.debug` is set: tile
    ownership, techniques held, and production limits."""
    check_tile_owner_invariants(sim)
    check_technique_invariants(sim)
    return check_capacity_invariants(sim)
