"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: a late-game household opens each benefaction, and the channel the work
declares moves the way it declares, its upkeep is real, closing it switches the effect off, and a scalable work comes in
bigger sizes at a higher price. What the branch declares is validated in test_complaint_190_benefactions; the gate on
prerequisites is test_research_start_gates."""
import json
import os

from .harness import *  # noqa: F401,F403

with open(os.path.join(S.ROOT, "data", "branches", "56_benefactions.json")) as _branch:
    WORKS = tuple(node["id"] for node in json.load(_branch))
PRESENT = [work for work in WORKS if work in NODES]
KEPT = [work for work in PRESENT if NODES[work]["up"] > 0]


def late_game_sim():
    """A rich household that already knows what every work needs and has hands to supervise them."""
    late = sim(capital=800_000_000.0)
    for work in PRESENT:
        late.done.update(NODES[work]["pre"])
    late._done_changed()
    # a work that names another going concern as its ground needs that concern open
    for work in PRESENT:
        for needed in NODES[work]["pre"]:
            if late.is_venture(needed):
                late.state.projects.operating.add(needed)
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
check("scenario benefactions: no work can be started without its prerequisites",
      not any(fresh.can_start(work) for work in PRESENT), [work for work in PRESENT if fresh.can_start(work)])
check("scenario benefactions: every work can be started once its prerequisites are known",
      all(late.can_start(work) for work in PRESENT), {work: late.start_reason(work)[1] for work in PRESENT if not late.can_start(work)})
listed = str(S._agent_dispatch(late, NODES, {"cmd": "available", "limit": 0, "all": True}))
check("scenario benefactions: `available` offers every one to a late-game household",
      bool(PRESENT) and all(work in listed for work in PRESENT), [work for work in PRESENT if work not in listed])
check("scenario benefactions: the paid-once works are knowledge, not going concerns, and the kept ones are concerns the engine counts",
      all(not late.is_venture(work) for work in PRESENT if work not in KEPT)
      and all(late.is_venture(work) and work in late.CAPABILITY_INSTITUTIONS for work in KEPT), KEPT)


# ---- what each one changes, through the channel it declares ----
def protection_of(house):
    house.update_protection()
    return house.state.household.protection


# One late-game household serves every work: each is opened, measured against the household just before, then closed
# again, so the next work starts from the same position.
SCHOOL_PRECONDITIONS = tuple(node_id for node_id, node in NODES.items()
                             if (node.get("mechanics") or {}).get("schooling_flow", {}).get("required"))
run_it(late, *SCHOOL_PRECONDITIONS)


def channel_probes(mechanics):
    """A probe per effect channel a work declares: which engine reading must move, and which way."""
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
wrong_way, upkeep_off, not_counted, not_switched_off = [], [], [], []
for work in KEPT:
    before = [probe(late) for _label, probe, _direction in PROBES[work]]
    run_it(late, work)
    for (label, probe, direction), value_before in zip(PROBES[work], before):
        value_after = probe(late)
        if not (value_after - value_before) * direction > 1e-9:
            wrong_way.append((work, label, value_before, value_after))
    # the upkeep is real, and closing the doors switches the effect off
    if not (abs(late.institution_upkeep(work) - late.nodes[work]["up"]) < 1e-6 * late.nodes[work]["up"]
            and late.nodes[work]["up"] > 0):
        upkeep_off.append(work)
    if not late.upkeep() >= late.institution_upkeep(work) - 1e-6:
        not_counted.append(work)
    label, probe, direction = PROBES[work][0]
    opened_value = probe(late)
    late.close_venture(work)
    if not abs(probe(late) - before[0]) < abs(opened_value - before[0]):
        not_switched_off.append((work, label, before[0], opened_value, probe(late)))
check("scenario benefactions: every kept work, once open, moves each channel it declares the intended way",
      not wrong_way, wrong_way)
check("scenario benefactions: every kept work costs its whole yearly upkeep when open, counted in what the household pays",
      not upkeep_off and not not_counted, (upkeep_off, not_counted))
check("scenario benefactions: closing a kept work takes its first channel back toward where it was",
      not not_switched_off, not_switched_off)

# ---- repeatable: a further unit of a scalable work is more of it, at a higher price ----
not_opening, not_again, not_more, not_dearer, upkeep_not_growing = [], [], [], [], []
for work in KEPT:
    if work not in late.SCALABLE_INSTITUTIONS:
        continue
    ok_first, message_first = late.open_venture(work)
    if not ok_first:
        not_opening.append((work, message_first))
        continue
    units_before = late.institution_units(work)
    second_unit_price = late.institution_unit_cost(work, units_before, 1.0)
    ok_more, message_more = late.open_venture(work, units=1.0)
    if not ok_more:
        not_again.append((work, message_more))
    else:
        if not late.institution_units(work) > units_before:
            not_more.append(work)
        if not second_unit_price > late.venture_capex(work):
            not_dearer.append(work)
        if not abs(late.institution_upkeep(work) - late.nodes[work]["up"] * late.institution_units(work)) < 1e-6 * late.nodes[work]["up"]:
            upkeep_not_growing.append(work)
    late.close_venture(work)
check("scenario benefactions: a scalable work opens, can be founded again on top of the first, and more of it runs",
      not not_opening and not not_again and not not_more, (not_opening, not_again, not_more))
check("scenario benefactions: a further unit costs more than the first did and upkeep grows with the units",
      not not_dearer and not upkeep_not_growing, (not_dearer, upkeep_not_growing))
