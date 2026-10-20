"""arrears_hours: a household in arrears must not lose the hours of a project that owes nothing further (Complaint:
"in arrears freezes ALL founder-hour progress even on fully-paid projects"), and a concern shut on purpose must
never reappear on its own. The rules are tested on built inputs (`project_funding`, `business_review.reopen`);
two named scenarios run them through the yearly step."""
from .harness import *  # noqa: F401,F403

from sim.agents import business_review
from sim.agents.api import Business
from sim.engine import project_funding

# --- the purse a project may draw on
check("the purse is capital and part of the credit line, less the shortfall of fixed costs over revenue",
      abs(project_funding.project_purse(1000.0, 500.0, 900.0, 400.0)
          - (1000.0 + 500.0 * project_funding.CREDIT_DRAW_SHARE - 500.0)) < 1e-9)
check("revenue that covers the fixed costs reserves nothing",
      project_funding.project_purse(1000.0, 0.0, 300.0, 400.0) == 1000.0)

# --- the year's funding of one project
nothing_owed = project_funding.fund_year(0.0, -5000.0, 400.0, 0.0, 500.0, True)
check("a project that owes nothing further is paid whole and keeps its hours, however deep the household's arrears",
      nothing_owed.money == 0.0 and nothing_owed.gave_back == 0.0 and nothing_owed.refunded == 0.0, nothing_owed)
check("...and it is not marked underfunded, because nothing was short", not nothing_owed.underfunded and nothing_owed.why is None)
covered = project_funding.fund_year(300.0, 300.0, 400.0, 0.0, 500.0, False)
check("a bill the purse covers is paid whole with no hours given back",
      covered.money == 300.0 and covered.gave_back == 0.0 and not covered.underfunded, covered)
half = project_funding.fund_year(400.0, 200.0, 500.0, 0.0, 500.0, False)
check("a bill beyond the purse is paid what the purse holds and gives back the hours of the unfunded part",
      half.money == 200.0 and half.gave_back == 250.0 and half.underfunded and half.refunded == 250.0, half)
broke = project_funding.fund_year(400.0, -100.0, 500.0, 0.0, 500.0, True)
check("a purse gone negative pays the project nothing and gives back every hour offered, but no more than was taken",
      broke.money == 0.0 and broke.gave_back == 500.0
      and project_funding.fund_year(400.0, -100.0, 300.0, 0.0, 500.0, True).gave_back == 300.0, broke)
check("hours already handed back by the trade shortage are not handed back twice",
      project_funding.fund_year(400.0, 0.0, 500.0, 400.0, 500.0, False).gave_back == 100.0
      and project_funding.fund_year(400.0, 0.0, 500.0, 500.0, 500.0, False).gave_back == 0.0)
check("the cause given is arrears when the household is in arrears, the instalment otherwise",
      broke.why == project_funding.WHY_IN_ARREARS and half.why == project_funding.WHY_INSTALMENT)
check("only hours lost while in arrears, and worth noticing, are reported as lost to arrears",
      broke.hours_lost_to_arrears == 500.0 and half.hours_lost_to_arrears == 0.0
      and project_funding.fund_year(400.0, 399.5, 500.0, 0.0, 500.0, True).hours_lost_to_arrears == 0.0)

# --- a concern shut on purpose is never reopened by the staffing rule
class Owner(business_review.Reviewable):
    """An owner that can staff anything."""

    def __init__(self, business):
        self.business = business

    def reopens_staffed_plant(self, entry_key, world):
        return True


plants = Business.running(["short_of_staff", "shut_by_player", "running"], opened_year=0)
plants.mothball("short_of_staff", 5, business_review.STAFF_SHORT)
plants.mothball("shut_by_player", 5, "player")
check("only the plants the staffing rule shut come back, and only when the owner can staff them; one shut on purpose never does",
      business_review.reopen(plants, Owner(plants), None) == ["short_of_staff"], business_review.reopen(plants, Owner(plants), None))

# --- scenario: a fully-paid project makes real hour progress through the yearly step while the household is in arrears
s_af = sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
             if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
# Injected directly into `active`, bypassing prerequisite legality: the allocation is under test, not the gate.
s_af.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0,
                          spent=s_af.project_cost(_af_k), cost_left=0.0,
                          lab_left=dict(_af_n["lab"]))
_lim_af = s_af.credit_limit()
_fixed_af = s_af.living_cost() + s_af.upkeep() + s_af.mine_operating_cost()
_reserve_af = max(0.0, _fixed_af - s_af.revenue())
# In arrears just deep enough for the project's purse to be negative (50 short), well clear of the credit limit
# (deeper debt costs interest, and at a high rate one year's alone could carry the household past the limit).
s_af.capital = min(-1.0, _reserve_af - 0.6 * _lim_af - 50.0)
_in_arrears_clear_of_limit = s_af.capital > -_lim_af and s_af.active[_af_k]["cost_left"] == 0.0
_ph_before_af = s_af.active[_af_k]["ph_left"]
s_af.step()
check("scenario: a fully-paid project still makes real hour progress through the year while the household is in "
      "arrears, and is not marked underfunded",
      _in_arrears_clear_of_limit and _af_k in s_af.active
      and s_af.active[_af_k]["ph_left"] < _ph_before_af - 100
      and not s_af.active[_af_k].get("underfunded_this_year"),
      (_in_arrears_clear_of_limit, _ph_before_af, s_af.active.get(_af_k, {}).get("ph_left"),
       s_af.active.get(_af_k, {}).get("why_underfunded")))


# --- scenario: the treadmill, measured: a spread of concerns starved of staff, closures against automatic reopenings
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
