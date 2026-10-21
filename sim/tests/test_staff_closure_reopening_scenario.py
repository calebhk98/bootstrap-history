"""Scenario: a spread of concerns starved of staff closes, and with auto_hire every closure comes back on its own once the
household can staff it again. The rule (only staffing closures, only when the owner can staff them) is tested on built
inputs in test_arrears_hours. Slow topic: a 25-concern game run for years.

Re-measure: `python3 -m sim.tests --slow --only staff_closure_reopening_scenario`."""
from .harness import *  # noqa: F401,F403


def _portfolio_run(auto_hire, years=12):
    sim_state = sim(civ="norse_900ad", capital=60000.0)
    sim_state.policy["auto_hire"] = auto_hire
    cands = sorted((node_id for node_id in NODES if sim_state.is_venture(node_id) and NODES[node_id]["rev"] > 0),
                   key=lambda k: -(NODES[k]["rev"] / max(1.0, sum(sim_state.venture_hands(k)))))
    chosen, need_sch, need_art = [], 0.0, 0.0
    for node_id in cands:
        sim_state.done.add(node_id)
        scholar_hands, artisan_hands = sim_state.venture_hands(node_id)
        if (need_sch + scholar_hands > 8.0 and need_sch > 0) or (need_art + artisan_hands > 35.0 and need_art > 0):
            sim_state.done.discard(node_id)
            continue
        need_sch += scholar_hands
        need_art += artisan_hands
        chosen.append(node_id)
        if len(chosen) >= 25:
            break
    sim_state._done_changed()
    sim_state.employees["scholar"] = round(need_sch) + 1
    sim_state.employees["artisan"] = round(need_art) + 2
    sim_state.labour._resync_pools()
    # one year's losses forced rather than left to the dice
    opened = [node_id for node_id in chosen if sim_state.open_venture(node_id)[0]]
    reopenings = 0
    for year in range(years):
        if year == 1:
            sim_state.employees["artisan"] = 2.0
            sim_state.labour._resync_pools()
        before = set(sim_state.operating)
        sim_state.step()
        reopenings += len((set(sim_state.operating) - before) & set(opened))
    free_scholars, free_artisans = sim_state.venture_staff_free()
    # only a staffing closure is the staffing rule's to undo
    stranded = [node_id for node_id in opened if node_id not in sim_state.operating
                and sim_state.staff_closure_age(node_id) is not None
                and sim_state.venture_hands(node_id)[0] <= free_scholars + 0.01
                and sim_state.venture_hands(node_id)[1] <= free_artisans + 0.01]
    return opened, stranded, reopenings


_opened, _stranded, _reopenings = _portfolio_run(auto_hire=True)
check("scenario: with auto_hire replacing attrition losses, no closed concern stays shut while there are free people "
      "to run it - every closure comes back on its own as soon as the household can staff it again",
      not _stranded and _reopenings > 0,
      "opened %d, shut with free staff at the end: %s, auto-reopenings: %d"
      % (len(_opened), _stranded, _reopenings))
