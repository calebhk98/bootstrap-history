"""Complaint 194: things a very rich founder can spend on.

Endowments, public works, patronage and display, commerce and finance, grants to the state and
expeditions are ordinary works declared in data (data/branches/56_benefactions.json). Each acts only
through mechanics channels the engine already reads (data/branches/MECHANICS.md), costs from its
labour and materials, and keeps costing upkeep for as long as it is open.
"""
from .harness import *

WORKS = (
    "ben_free_school_foundation", "ben_public_library", "ben_research_foundation",
    "ben_hospital_foundation", "ben_civic_water_works", "ben_harbour_and_lighthouse",
    "ben_telegraph_network", "ben_public_games", "ben_temple_endowment",
    "ben_scholar_and_artist_patronage", "ben_house_bank", "ben_underwriting_syndicate",
    "ben_grain_dole", "ben_state_subvention", "ben_survey_and_trade_expedition",
)
PRESENT = [work for work in WORKS if work in NODES]

for work in WORKS:
    check("%s is in the tree" % work, work in NODES)
check("the first set of benefactions is in the tree", len(PRESENT) == len(WORKS),
      sorted(set(WORKS) - set(PRESENT)))


def late_game_sim():
    """A rich household that already knows what every work needs and has hands to supervise them."""
    late = sim(capital=800_000_000.0)
    for work in PRESENT:
        late.done.update(NODES[work]["pre"])
    late._done_changed()
    for work in PRESENT:
        for trade in NODES[work]["lab"]:
            late.state.household.trades_created.add(trade)
            late.employees[trade] = max(late.employees.get(trade, 0.0), 20.0)
    late.employees["scholar"] = 40.0
    late.employees["artisan"] = 80.0
    late._resync_pools()
    return late


def baseline(*running):
    base = late_game_sim()
    run_it(base, *running)
    return base


# ---- the works are available once their prerequisites are met, and not before ----
fresh = sim(capital=800_000_000.0)
late = late_game_sim()
for work in PRESENT:
    check("%s cannot be started without its prerequisites" % work, not fresh.can_start(work))
    check("%s can be started once its prerequisites are known" % work, late.can_start(work),
          late.start_reason(work)[1])
listing = S._agent_dispatch(late, NODES, {"cmd": "available", "limit": 0, "all": True})
listed = str(listing)
check("`available` offers the benefactions to a late-game household",
      bool(PRESENT) and all(work in listed for work in PRESENT), [w for w in PRESENT if w not in listed])

# ---- each is a costed, non-earning, upkeep-bearing work built from labour and materials ----
for work in PRESENT:
    node = NODES[work]
    check("%s earns nothing of its own" % work, node["rev"] == 0)
    check("%s is built from labour and materials, not a bare capital figure" % work,
          node["_labour_cost"] > 0 and node["_material_cost"] > 0 and node["cap"] == 0)
    check("%s costs upkeep at least as large as a maintenance share of its build" % work,
          node["up"] >= 0.02 * (node["_labour_cost"] + node["_material_cost"]) * 0.99, node["up"])
    check("%s is a going concern, not knowledge" % work, late.is_venture(work))
    check("%s declares mechanics" % work, bool(node.get("mechanics")))
    check("%s is a kept, not free, institution" % work,
          work in late.CAPABILITY_INSTITUTIONS)

# ---- what each one changes, through the channel it declares ----
def opened(work, extra_running=()):
    """A household with `work` built and its doors open."""
    house = baseline(*extra_running)
    run_it(house, work)
    return house


def protection_of(house):
    house.update_protection()
    return house.state.household.protection


PROBES = {
    "ben_free_school_foundation": [("schooling flow", lambda h: h._schooling_flow(), 1, ("school_founded",)),
                                   ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_public_library": [("schooling flow", lambda h: h._schooling_flow(), 1, ("school_founded",)),
                           ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_research_foundation": [("scholars the household can keep", lambda h: h.staff_capacity()[0], 1, ()),
                                ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_hospital_foundation": [("loss of people to sickness", lambda h: h.hazard_relief("staff_loss")[0], -1, ()),
                                ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_civic_water_works": [("loss of people to sickness", lambda h: h.hazard_relief("staff_loss")[0], -1, ()),
                             ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_harbour_and_lighthouse": [("market reach", lambda h: h.goods_reach_factor(), 1, ()),
                                   ("losses at sea", lambda h: h.hazard_relief("output_factor")[0], -1, ()),
                                   ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_telegraph_network": [("market reach", lambda h: h.goods_reach_factor(), 1, ()),
                              ("people one can direct", lambda h: h.supervision_room(), 1, ())],
    "ben_public_games": [("protection", protection_of, 1, ()),
                         ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_temple_endowment": [("protection", protection_of, 1, ()),
                             ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_scholar_and_artist_patronage": [("standing", lambda h: h.standing_floor(), 1, ()),
                                         ("scholars the household can keep", lambda h: h.staff_capacity()[0], 1, ())],
    "ben_house_bank": [("credit limit", lambda h: h.credit_limit(), 1, ())],
    "ben_underwriting_syndicate": [("losses", lambda h: h.hazard_relief("output_factor")[0], -1, ())],
    "ben_grain_dole": [("protection", protection_of, 1, ()),
                       ("loss of people to sickness", lambda h: h.hazard_relief("staff_loss")[0], -1, ()),
                       ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_state_subvention": [("protection", protection_of, 1, ()),
                             ("standing", lambda h: h.standing_floor(), 1, ())],
    "ben_survey_and_trade_expedition": [("market reach", lambda h: h.goods_reach_factor(), 1, ()),
                                        ("standing", lambda h: h.standing_floor(), 1, ())],
}
for work in PRESENT:
    for label, probe, direction, needs in PROBES[work]:
        before = probe(baseline(*needs))
        after = probe(opened(work, needs))
        moved = (after - before) * direction
        check("%s open changes %s the intended way" % (work, label), moved > 1e-9, (before, after))

# ---- closing the doors switches the effect off; the upkeep is real ----
for work in PRESENT:
    house = opened(work)
    check("%s costs its whole yearly upkeep when open, whatever the household headcount" % work,
          abs(house.institution_upkeep(work) - house.nodes[work]["up"]) < 1e-6 * house.nodes[work]["up"]
          and house.nodes[work]["up"] > 0)
    check("%s upkeep is counted in what the household pays each year" % work,
          house.upkeep() >= house.institution_upkeep(work) - 1e-6)
    plain = baseline()
    for label, probe, direction, needs in PROBES[work][:1]:
        if needs:
            continue
        opened_value = probe(house)
        house.close_venture(work)
        check("%s: closing it takes %s back to where it was" % (work, label),
              abs(probe(house) - probe(plain)) < abs(opened_value - probe(plain)), (opened_value, probe(house)))

# ---- repeatable: a further unit of a scalable work is more of it, at a higher price ----
for work in PRESENT:
    if work not in late.SCALABLE_INSTITUTIONS:
        continue
    house = late_game_sim()
    house.done.add(work)
    house._done_changed()
    ok_first, message_first = house.open_venture(work)
    check("%s opens" % work, ok_first, message_first)
    if not ok_first:
        continue
    units_before = house.institution_units(work)
    second_unit_price = house.institution_unit_cost(work, units_before, 1.0)
    ok_more, message_more = house.open_venture(work, units=1.0)
    check("%s can be founded again on top of the first" % work, ok_more, message_more)
    if ok_more:
        check("%s: more of it runs after expanding" % work, house.institution_units(work) > units_before)
        check("%s: a further unit costs more than the first did" % work,
              second_unit_price > house.venture_capex(work))
        check("%s: upkeep grows with the units" % work,
              abs(house.institution_upkeep(work)
                  - house.nodes[work]["up"] * house.institution_units(work)) < 1e-6 * house.nodes[work]["up"]
              and house.institution_units(work) > units_before)
