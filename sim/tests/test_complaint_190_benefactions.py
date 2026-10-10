"""Complaint 190: things a very rich founder can spend on.

Endowments, public works, patronage and display, commerce and finance, grants to the state and
expeditions are ordinary works declared in data (data/branches/56_benefactions.json). Each acts only
through mechanics channels the engine already reads (data/branches/MECHANICS.md), costs from its
labour and materials, and keeps costing upkeep for as long as it is open.
"""
import json
import os

from .harness import *

with open(os.path.join(S.ROOT, "data", "branches", "56_benefactions.json")) as _branch:
    WORKS = tuple(node["id"] for node in json.load(_branch))
PRESENT = [work for work in WORKS if work in NODES]
# a work with a yearly programme is kept up; one without is paid for once (a transfer, a charter) and is knowledge after
KEPT = [work for work in PRESENT if NODES[work].get("annual_labour_hours")]
ONCE = [work for work in PRESENT if work not in KEPT]

check("every work declared in the benefactions branch reaches the tree and there is at least one",
      bool(WORKS) and len(PRESENT) == len(WORKS), sorted(set(WORKS) - set(PRESENT)))


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
    late.labour._resync_pools()
    return late


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

# ---- each is a costed, non-earning work built from labour; a kept one bears upkeep and a once-paid one none ----
check("some works are paid once and the rest are kept up", bool(ONCE) and bool(KEPT), (ONCE, KEPT))
for work in ONCE:
    node = NODES[work]
    check("%s earns nothing and costs nothing to keep: it is paid once" % work,
          node["rev"] == 0 and node["up"] == 0 and not late.is_venture(work), (node["rev"], node["up"]))
    check("%s costs labour to bring about" % work, node["_labour_cost"] > 0 and node["cap"] == 0)
    check("%s declares mechanics" % work, bool(node.get("mechanics")))
for work in KEPT:
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
# One late-game household serves every work: each is opened, measured against the household just
# before, then closed again, so the next work starts from the same position.
def protection_of(house):
    house.update_protection()
    return house.state.household.protection


# A probe per effect channel a work declares: which engine reading must move, and which way.
SCHOOL_PRECONDITIONS = tuple(node_id for node_id, node in NODES.items()
                             if (node.get("mechanics") or {}).get("schooling_flow", {}).get("required"))
run_it(late, *SCHOOL_PRECONDITIONS)


def channel_probes(mechanics):
    probes = []
    if "schooling_flow" in mechanics:
        probes.append(("schooling flow", lambda h: h._schooling_flow(), 1))
    if "standing" in mechanics:
        probes.append(("standing", lambda h: h.standing_floor(), 1))
    if (mechanics.get("staff_capacity") or {}).get("scholars"):
        probes.append(("scholars the household can keep", lambda h: h.labour.staff_capacity()[0], 1))
    for counter in mechanics.get("hazard_counters") or []:
        probes.append(("loss to %s" % counter["kind"],
                       lambda h, kind=counter["kind"]: h.hazard_relief(kind)[0], -1))
    if "reach" in mechanics:
        probes.append(("market reach", lambda h: h.goods_reach_factor(), 1))
    if "supervision_room" in mechanics:
        probes.append(("people one can direct", lambda h: h.labour.supervision_room(), 1))
    if "protection" in mechanics or "patron_protection" in mechanics:
        probes.append(("protection", protection_of, 1))
    if "credit_line" in mechanics:
        probes.append(("credit limit", lambda h: h.credit_limit(), 1))
    return probes


PROBES = {work: channel_probes(NODES[work]["mechanics"]) for work in KEPT}
for work in KEPT:
    check("%s declares at least one effect channel this test can measure" % work, bool(PROBES[work]))

for work in KEPT:
    before = [probe(late) for _label, probe, _direction in PROBES[work]]
    run_it(late, work)
    for (label, probe, direction), value_before in zip(PROBES[work], before):
        value_after = probe(late)
        check("%s open changes %s the intended way" % (work, label),
              (value_after - value_before) * direction > 1e-9, (value_before, value_after))
    # ---- the upkeep is real, and closing the doors switches the effect off ----
    check("%s costs its whole yearly upkeep when open, whatever the household headcount" % work,
          abs(late.institution_upkeep(work) - late.nodes[work]["up"]) < 1e-6 * late.nodes[work]["up"]
          and late.nodes[work]["up"] > 0)
    check("%s upkeep is counted in what the household pays each year" % work,
          late.upkeep() >= late.institution_upkeep(work) - 1e-6)
    label, probe, direction = PROBES[work][0]
    opened_value = probe(late)
    late.close_venture(work)
    check("%s: closing it takes %s back to where it was" % (work, label),
          abs(probe(late) - before[0]) < abs(opened_value - before[0]), (before[0], opened_value, probe(late)))

# ---- repeatable: a further unit of a scalable work is more of it, at a higher price ----
for work in KEPT:
    if work not in late.SCALABLE_INSTITUTIONS:
        continue
    ok_first, message_first = late.open_venture(work)
    check("%s opens" % work, ok_first, message_first)
    if not ok_first:
        continue
    units_before = late.institution_units(work)
    second_unit_price = late.institution_unit_cost(work, units_before, 1.0)
    ok_more, message_more = late.open_venture(work, units=1.0)
    check("%s can be founded again on top of the first" % work, ok_more, message_more)
    if ok_more:
        check("%s: more of it runs after expanding" % work, late.institution_units(work) > units_before)
        check("%s: a further unit costs more than the first did" % work,
              second_unit_price > late.venture_capex(work))
        check("%s: upkeep grows with the units" % work,
              abs(late.institution_upkeep(work)
                  - late.nodes[work]["up"] * late.institution_units(work)) < 1e-6 * late.nodes[work]["up"]
              and late.institution_units(work) > units_before)
    late.close_venture(work)
