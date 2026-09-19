"""arrears_hours: regression checks, run individually with `--only arrears_hours`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# BREAK, REPORTED INDEPENDENTLY ON THREE CIVILISATIONS: "in arrears freezes
# ALL founder-hour progress even on fully-paid projects." Confirmed exactly:
# step()'s hour-allocation guarded the year's money draw with `if money >
# purse`, where `purse` is the household's own affordability (capital plus
# part of credit, less fixed costs) - but a project whose cost_left is
# already 0 asks for money=0 this YEAR, and 0 > purse is still true whenever
# the HOUSEHOLD'S purse has gone negative, nothing to do with this project's
# own bill. That forced funded_frac to 0.0 and refunded nearly the whole
# year's hours on a project that needed not one more denarius - a pure
# calendar wait turned into no progress at all, for as long as the
# household stayed in arrears, however long that ran.
# =============================================================================
s_af = sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
             if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
# Injected directly into `active`, bypassing prerequisite legality, to
# isolate step()'s hour-allocation arithmetic from whether this particular
# node could be started today - the bug is in the allocation, not the gate.
s_af.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0,
                          spent=s_af.project_cost(_af_k), cost_left=0.0,
                          lab_left=dict(_af_n["lab"]))
_lim_af = s_af.credit_limit()
_fixed_af = s_af.living_cost() + s_af.upkeep() + s_af.mine_operating_cost()
_reserve_af = max(0.0, _fixed_af - s_af.revenue())
# Mildly in arrears - well clear of credit_limit (so enforce_credit_limit
# does not wipe `active` out from under this check), but still enough for
# THIS PROJECT's own purse (capital + 0.6*limit - reserve) to be negative.
s_af.capital = -(_reserve_af + 0.6 * _lim_af) - 50.0
check("set-up: in arrears, but nowhere near the credit limit itself, with "
      "a project that owes nothing further",
      s_af.capital > -_lim_af
      and s_af.active[_af_k]["cost_left"] == 0.0, s_af.capital)
_ph_before_af = s_af.active[_af_k]["ph_left"]
s_af.step()
check("a fully-paid project still makes real hour progress while the "
      "household is in arrears, rather than being refunded almost "
      "everything it was offered for a shortfall that is not its own",
      _af_k in s_af.active
      and s_af.active[_af_k]["ph_left"] < _ph_before_af - 100,
      (_ph_before_af, s_af.active.get(_af_k, {}).get("ph_left")))
check("...and it is not marked underfunded, because nothing was actually "
      "short - there was nothing left to pay for",
      not s_af.active.get(_af_k, {}).get("underfunded_this_year"),
      s_af.active.get(_af_k, {}).get("why_underfunded"))

# ANY VENTURE AN ARTISAN CAN STAFF WILL DO. The checks below are about
# reopen_restaffed_ventures and mothball, not about this node: cementation
# steel is named because it is staffable, not because anything here depends
# on it. Swap it for another artisan-staffable venture and the checks still
# mean what they say.
_node_id = "cementation_steel"

# --- and a concern a player shut ON PURPOSE must never reappear on its own -
# reopen_restaffed_ventures only undoes close_unstaffed_ventures, never `mothball`
s = sim(capital=50000.0)
s.done.add(_node_id)
s._done_changed()
s.employees["artisan"] = 6.0
s._resync_pools()
s.open_venture(_node_id)
s.mothball_work(_node_id)
reopened = s.reopen_restaffed_ventures(s.year)
check("a concern closed on purpose with 'mothball' is never auto-reopened, "
      "however much staff is free - that is still the player's call",
      reopened == [] and _node_id in s.mothballed and _node_id not in s.operating,
      reopened)

# --- the treadmill itself, measured: build a realistic spread of concerns,
# starve them of any staff replacement (auto_hire off, the player default),
# and count closures against automatic reopenings over 40 years
def _portfolio_run(auto_hire, years=40):
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
    sim_state._resync_pools()
    opened = [node_id for node_id in chosen if sim_state.open_venture(node_id)[0]]
    reopenings = 0
    for _ in range(years):
        before = set(sim_state.operating)
        sim_state.step()
        reopenings += len((set(sim_state.operating) - before) & set(opened))
    return opened, sum(1 for node_id in opened if node_id in sim_state.operating), reopenings

_opened, _open_end, _reopenings = _portfolio_run(auto_hire=True)
check("with auto_hire replacing attrition losses, the portfolio it built "
      "fully recovers over 40 years - every closure eventually comes back "
      "on its own once the household can staff it again",
      _open_end == len(_opened) and _reopenings > 0,
      "opened %d, open at year 40: %d, auto-reopenings: %d"
      % (len(_opened), _open_end, _reopenings))
