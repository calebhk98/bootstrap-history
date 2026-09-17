"""Scoring the run, at any point or at the end: score_report, final_report, and the components behind them."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim

from .state import _agent_end_reason
from .util import _fmt_num, _wrap




def final_report(s, nodes):
    """The scoreboard, once the run is over.

    Two play testers finished long runs and got one sentence - "you built 1944
    things and did not reach point-contact transistor" - then a queue of
    identical refusals. One started a whole second game with the fog off and
    ran `path` just to learn that the goal is 142 nodes deep and which one
    they had stopped at. That is a question the game should answer when there
    is nothing left to spoil: the run is finished, so showing the road is the
    reward for finishing it, not a leak.
    """
    goal = getattr(s, "goal", None)
    earned = sorted(s.done - s.granted)
    out = {"ended_in": s.year, "why": _agent_end_reason(s),
           "you_built": len(earned),
           "this_society_already_had": len(s.granted),
           "money": round(s.capital, 1),
           "people": round(s.headcount(), 1),
           "reputation": round(s.reputation, 1),
           "concerns_you_were_running": len(getattr(s, "operating", ())),
           "failed_attempts": sum(getattr(s, "failed_attempts", {}).values())}
    if goal and goal in nodes:
        need = closure(nodes, goal)
        left = [x for x in topo_order(nodes, need) if x not in s.done]
        out["the_goal"] = goal
        out["reached_it"] = bool(s.goal_year)
        out["the_whole_road_was"] = len(need)
        out["you_had_%d_of_them" % (len(need) - len(left))] = len(need) - len(left)
        out["still_to_build_when_it_ended"] = len(left)
        # The next few steps you never took, in the order you would have taken
        # them. Under fog this is the first sight of the road; the run is over.
        out["the_next_things_would_have_been"] = left[:8]
        out["and_the_last_step"] = goal
    biggest = sorted(earned, key=lambda k: -nodes[k]["_total_cost"])[:6]
    out["the_largest_things_you_built"] = biggest
    # THE SCORE, ON THE SAME SCREEN. The run is over, so the tree's total
    # size is never withheld here (score_report's own reveal_tree_total is
    # (not fog) or ended, and by the time final_report runs it is always
    # ended) - see score_report and _score_components for what feeds it.
    out["score"] = score_report(s, nodes)
    return out


# ---------------------------------------------------------------------------
# THE SCORE. A player who had just won asked for one number, weighted across
# seven things they named, plus a short list of achievements. Every raw
# value below is something the engine already tracks for a DIFFERENT reason
# (state, final_report, the risk and labour screens) - nothing here is a new
# ledger invented to make the formula prettier. See each component's own
# comment for exactly which field feeds it and why that is a fair reading of
# the category the player named, and see the commit/report for which of
# these are mechanically bounded (no tuning possible) versus anchored by
# judgement against the one real high-water mark available, the 599 AD save.
# ---------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "technology_coverage": 0.35,
    "literacy": 0.15,
    "workforce": 0.15,
    "economy": 0.10,
    "institutions": 0.10,
    "resilience": 0.10,
    "standing": 0.05,
}


def _score_goal_floor_years(s, nodes):
    """The goal's own critical-path floor, in years - the fastest any run of
    any civilisation could reach it with unlimited money and one director
    (data.critical_path, civ-independent by construction: see its own
    docstring). Cached on the Sim the same way `final_report`'s
    `_goal_closure` already caches the goal's prerequisite set, because this
    walks the whole closure and `score` is meant to be called often.
    """
    cached = getattr(s, "_goal_critical_floor", None)
    if cached is not None:
        return cached
    goal = getattr(s, "goal", None)
    if not goal or goal not in nodes:
        return None
    try:
        yrs, _chain = critical_path(nodes, goal)
    except Exception:
        return None
    s._goal_critical_floor = yrs
    return yrs


def _score_components(s, nodes, reveal_tree_total):
    """The seven weighted components, each {"raw", "normalized", "weight",
    "weighted"} - raw in the quantity's own natural unit, normalized the
    0..1 figure the weight actually multiplies.

    `reveal_tree_total` is True off fog, or once the run has ended - the
    same two-part condition final_report's own "the TOTAL is the size of
    the tree's own spoiler surface" comment already uses for the goal's
    road, applied here to the bigger spoiler: the size of the WHOLE tree.
    done_count is visible in `state` under fog regardless, so showing
    done/total under fog mid-run would hand back the withheld total by
    division - this is the one place that has to check.
    """
    out = {}

    # TECHNOLOGY COVERAGE (35%) - done / the WHOLE tree, not done / the
    # goal's own closure. The goal's closure is 1 to 201 nodes of the tree
    # (goal_catalog, 17 goals) and reaching it no longer ends the run - see
    # _agent_end_reason's own comment: a won run has "barely touched" the
    # tree, and the default horizon (500 years) is comfortably more than
    # twice the longest goal floor (142 years), so every goal, however small
    # its own closure, leaves centuries to keep building before death or the
    # horizon actually ends the run. A goal-relative fraction would jump to
    # 1.0 the instant the goal completes and sit there for the rest of a
    # long run, which throws away 35% of the score's discriminating power
    # for exactly the "the tree is the real game, the goal is a gate" shape
    # this engine is built around. This is already a true fraction - 0 with
    # nothing built, 1 with the whole tree - so it needs no further anchor.
    if reveal_tree_total:
        total = len(nodes)
        raw = len(s.done)
        normalized = min(1.0, raw / total) if total else 0.0
        out["technology_coverage"] = {"raw": raw, "of_total": total,
                                       "normalized": normalized}
    else:
        out["technology_coverage"] = {
            "raw": len(s.done), "of_total": None, "normalized": None,
            "withheld": ("the tree's total size is the one thing fog keeps "
                         "from you; this resolves once the run ends")}

    # LITERACY (15%) - general and elite literacy against the CEILING each
    # already has in this engine (SocietyMixin.literacy_ceiling_general/
    # _elite, society.py): a hard, population- and mechanisation-driven cap
    # that is the same structural number for every civilisation, not
    # something this file tunes. 0.90 general / 0.97 elite are what the
    # mechanism itself says a pre-transistor-era society can ever reach, so
    # "literacy" here means how much of what is ACTUALLY reachable has been
    # reached, not a raw fraction a civilisation starting with worse
    # schooling could never max out. Weighted equally between the two
    # populations the engine tracks separately.
    gen = max(0.0, float(s.civ.get("literacy_general", 0.0)))
    gen_ceiling = max(1e-9, s.literacy_ceiling_general())
    eli = max(0.0, float(s.civ.get("literacy_elite", 0.0)))
    eli_ceiling = max(1e-9, s.literacy_ceiling_elite())
    lit_norm = 0.5 * min(1.0, gen / gen_ceiling) + 0.5 * min(1.0, eli / eli_ceiling)
    out["literacy"] = {"raw": round(gen, 4),
                        "raw_detail": {"general": round(gen, 4),
                                       "general_ceiling": round(gen_ceiling, 4),
                                       "elite": round(eli, 4),
                                       "elite_ceiling": round(eli_ceiling, 4)},
                        "normalized": lit_norm}

    # WORKFORCE (15%) - headcount(), the same aggregate final_report already
    # reports as "people" (employees plus slaves plus freedmen; labour.py).
    # Population has no mechanical ceiling this engine states outright the
    # way literacy does, so this is the one honest anchor available: a
    # log scale (a second thousand employees is not as meaningful as the
    # first) against a round number with headroom above the one real
    # high-water mark on record, the 599 AD calibration save's 691.7 - NOT
    # that save's own figure, so the save does not define 100% by
    # construction. 7,000 is ten times 691.7, rounded to a clean figure.
    WORKFORCE_ANCHOR = 7000.0
    headcount = max(0.0, s.headcount())
    work_norm = min(1.0, math.log1p(headcount) / math.log1p(WORKFORCE_ANCHOR))
    out["workforce"] = {"raw": round(headcount, 1), "normalized": work_norm}

    # ECONOMY (10%) - capital, but never as a bare denarius figure: each
    # civilisation's currency is a different scale (civs/*.json: "denarius",
    # "wu zhu cash", "hacksilver by weight", "cacao bean and cotton cloth",
    # each with its own wage_index/price_index multiplier on the shared wage
    # table, data.ANNUAL_WAGE) - comparing raw capital across civilisations
    # would be comparing different units with the same name. Deflating by
    # one ordinary worker-year IN THIS CIVILISATION'S OWN MONEY (an
    # artisan's annual wage, scaled by this civ's live price_index and
    # wage_index - the same two multipliers economy.py and labour.py price
    # everything else with) turns capital into a currency-free "years of an
    # ordinary worker's wage this fortune could buy", which is comparable
    # across civilisations. Log-scaled for the same reason as workforce,
    # against the same methodology: a round anchor ten times the
    # calibration save's 4.41 million worker-years, rounded to a clean
    # figure (50 million), not that save's own number.
    ECONOMY_ANCHOR_WORKER_YEARS = 50_000_000.0
    reference_wage = max(1e-6, ANNUAL_WAGE.get("artisan", 250.0)
                          * max(1e-6, float(getattr(s, "price_index", 1.0)))
                          * max(1e-6, float(getattr(s, "wage_index", 1.0))))
    worker_years = max(0.0, s.capital) / reference_wage
    econ_norm = min(1.0, math.log1p(worker_years)
                    / math.log1p(ECONOMY_ANCHOR_WORKER_YEARS))
    out["economy"] = {"raw": round(s.capital, 1),
                       "raw_detail": {"worker_years_equivalent":
                                      round(worker_years, 1)},
                       "normalized": econ_norm}

    # INSTITUTIONS (10%) - every CAPABILITY_INSTITUTIONS node (projects.py:
    # the fixed roster every running()/auto-open rule in the engine already
    # checks against), scored by institution_units()/institution_unit_ceiling()
    # for the five that scale (workshop, school, academy, collegium,
    # freedman staff - each ceiling already population- and literacy-driven,
    # the same mechanism literacy's own ceiling uses) and by a plain
    # running() boolean for the rest, which this engine models as one-off
    # achievements rather than a quantity (a patronage, a written corpus, a
    # power grid). sorted() because this sums floats over what would
    # otherwise be a frozenset, and PYTHONHASHSEED must not move the sum.
    inst_keys = sorted(s.CAPABILITY_INSTITUTIONS)
    inst_vals = []
    for k in inst_keys:
        if k in s.SCALABLE_INSTITUTIONS:
            ceiling = max(1.0, s.institution_unit_ceiling(k))
            inst_vals.append(min(1.0, s.institution_units(k) / ceiling))
        else:
            inst_vals.append(1.0 if s.running(k) else 0.0)
    inst_norm = (sum(inst_vals) / len(inst_vals)) if inst_vals else 0.0
    out["institutions"] = {"raw": sum(1 for value in inst_vals if value > 0.0),
                            "of_total": len(inst_vals),
                            "normalized": inst_norm}

    # RESILIENCE (10%) - an equally-weighted average of five fractions, each
    # a real, already-saved field read against a real threshold, none of
    # them invented for this screen:
    #   - corpus_preserved: 1 - forgotten / (done + forgotten). `forgotten`
    #     (society.py's _shocks, set nowhere else) is every technology a
    #     sacking actually destroyed; this is the share of everything ever
    #     completed that still stands.
    #   - solvent_share: 1 - insolvent_years / years elapsed. insolvent_years
    #     is a running count economy.py already keeps.
    #   - staffing_share: 1 - (distinct years close_unstaffed_ventures fired)
    #     / years elapsed. shut_for_staff (projects.py) is {node: year};
    #     distinct years, not count of concerns, because closing four
    #     concerns in one bad year is one bad year, not four.
    #   - scandal_margin: 1 - scandal / suspicion_danger, the exact ratio
    #     `state` already reports as "chance_of_being_denounced_this_year"'s
    #     own numerator and denominator.
    #   - founder_share: 1.0 if founder_alive else 0.0 - only ever
    #     discriminating in mortal play; harmless (always 1.0) under the
    #     immortal default.
    # Each is already a fraction of a real total, so none of these five
    # needs a chosen anchor the way workforce/economy do.
    run_years = max(1.0, s.year - s.cfg.get("start_year", s.year))
    forgotten_n = len(getattr(s, "forgotten", None) or {})
    ever_completed = len(s.done) + forgotten_n
    corpus_preserved = (1.0 - forgotten_n / ever_completed) if ever_completed else 1.0
    solvent_share = 1.0 - min(1.0, getattr(s, "insolvent_years", 0) / run_years)
    shut_years = len(set((getattr(s, "shut_for_staff", None) or {}).values()))
    staffing_share = 1.0 - min(1.0, shut_years / run_years)
    suspicion_danger = max(1e-9, float(s.cfg.get("suspicion_danger", 25.0)))
    scandal_margin = 1.0 - min(1.0, max(0.0, s.scandal) / suspicion_danger)
    founder_share = 1.0 if s.founder_alive else 0.0
    res_parts = [corpus_preserved, solvent_share, staffing_share,
                 scandal_margin, founder_share]
    res_norm = sum(res_parts) / len(res_parts)
    out["resilience"] = {"raw": sum(1 for value in res_parts if value >= 0.999),
                          "of_total": len(res_parts), "normalized": res_norm}

    # STANDING (5%) - reputation alone, not eminence: eminence is a danger
    # signal (how close you sit to being confiscated or denounced for being
    # too visible - see `prominence`/eminence_report), the opposite of a
    # score you want to maximise, where reputation (0..100 by construction;
    # projects.py clamps it at 100) is this engine's own plain measure of
    # standing.
    rep = max(0.0, min(100.0, s.reputation))
    out["standing"] = {"raw": round(rep, 1), "normalized": rep / 100.0}

    for name, weight in SCORE_WEIGHTS.items():
        comp = out[name]
        comp["weight"] = weight
        comp["weighted"] = (round(comp["normalized"] * weight, 4)
                            if comp["normalized"] is not None else None)
    return out


def _score_achievements(s, nodes):
    """Won-run achievements, each a plain condition on a field the engine
    already saves across sittings (SAVE_FIELDS, this file) - so each one is
    true of the WHOLE run, not just whatever is in memory right now. None of
    these reads failed_attempts: that counter is real (projects.py) but is
    NOT in SAVE_FIELDS, so it silently resets to empty every time a session
    is resumed from disk - the normal way this game is played (cli.py
    autosaves after every command). An achievement built on it would read
    "flawless" for any run that was ever closed and reopened, which is not
    an achievement, it is a bug in what gets remembered. See the report.
    """
    goal = getattr(s, "goal", None)
    won = bool(goal and s.goal_year)
    out = {}
    if not won:
        return out
    out["corpus_intact"] = {
        "won": len(getattr(s, "forgotten", None) or {}) == 0,
        "what": "the corpus was never diminished by a sacking"}
    out["never_understaffed"] = {
        "won": len(getattr(s, "shut_for_staff", None) or {}) == 0,
        "what": "no concern ever closed for want of staff"}
    out["clean_ledger"] = {
        "won": (getattr(s, "insolvent_years", 0) == 0
                and getattr(s, "interest_paid", 0.0) <= 0.0),
        "what": "never spent a year insolvent or paid a denarius of interest"}
    out["free_hands_only"] = {
        "won": (s.slaves == 0 and getattr(s, "manumitted_total", 0) == 0),
        "what": "built it without ever owning a slave"}
    floor = _score_goal_floor_years(s, nodes)
    out["outpaced_the_fastest_plan"] = {
        "won": bool(floor and (s.goal_year - s.cfg["start_year"]) <= 2.0 * floor),
        "what": ("reached the goal within twice its own fastest possible "
                 "timeline (%s years, one director, unlimited money)"
                 % _fmt_num(floor) if floor else "the goal's floor is unknown")}
    return out


def score_report(s, nodes):
    """The full score: the gate, the seven weighted components, the total,
    and the achievements - read by both the `score` command (any time) and
    the ending screen (final_report, below).
    """
    end_reason = _agent_end_reason(s)
    reveal_tree_total = (not getattr(s, "fog", False)) or (end_reason is not None)
    components = _score_components(s, nodes, reveal_tree_total)
    goal = getattr(s, "goal", None)
    goal_reached = bool(goal and s.goal_year)
    total = None
    if goal_reached and all(c["normalized"] is not None for c in components.values()):
        total = round(sum(c["weighted"] for c in components.values()), 4)
    # A NUMBER TO COMPARE RUNS WITH, NOT ONLY A PERCENTAGE. A player asked
    # for exactly this: a percentage answers "how much of the possible
    # score", a point figure answers "how did this run do against that
    # one", and the second question is what a player comparing two
    # civilisations or two seeds is actually asking.
    #
    # STILL CAPPED, ON PURPOSE. `total` above can never exceed 1.0: every
    # one of the seven components clamps its own "normalized" figure to
    # [0, 1] before the weights (SCORE_WEIGHTS, which sum to exactly 1.0)
    # are applied, so there is no way to run one component past its own
    # ceiling and buy points nowhere else has to pay for - a literacy of
    # 400% is not four times as literate, and an uncapped score would make
    # farming whichever single component is cheapest to overdrive the
    # dominant strategy, not balanced achievement across all seven. POINTS
    # is a plain, lossless rescaling of the SAME capped `total` - it is
    # not a second, less honest score computed some other way.
    #
    # 1,000 POINTS FOR A PERFECT RUN, chosen over the obvious alternative
    # of just multiplying the percentage by 100 (which would only ever
    # repeat a number already on the screen) for two reasons: a three-digit
    # spread (0-1000) reads, at a glance, as a score rather than a percent
    # sign that fell off, the way golf strokes or exam marks out of a
    # thousand do; and it carries exactly one more digit of resolution than
    # the percentage already shows (1 point = 0.1%), which is as much
    # precision as a figure built from normalized fractions and fixed
    # weights honestly has - inventing a bigger scale would imply the
    # model can discriminate finer than it does.
    points = round(total * 1000) if total is not None else None
    out = {"goal_in_words": (s.nodes[goal]["name"] if goal in getattr(s, "nodes", {})
                             else None),
           "goal_reached": goal_reached, "goal_year": s.goal_year,
           "end_reason": end_reason,
           "components": components, "total": total, "points": points,
           "points_scale": "0-1000, 1000 for a perfect run across every "
                           "component - the same capped total above, "
                           "rescaled for a figure to compare runs with, "
                           "not a second score computed differently"}
    if not goal_reached:
        out["no_score"] = "the goal was not reached"
    out["achievements"] = _score_achievements(s, nodes)
    return out


_SCORE_COMPONENT_ORDER = ("technology_coverage", "literacy", "workforce",
                          "economy", "institutions", "resilience", "standing")


def _score_lines(out, indent="  "):
    """The component table, the total and the achievements, as plain text -
    shared by `score` (render_score) and the ending screen (render_final),
    so there is exactly one rendering of a score to fall out of step.
    """
    L = []
    if not out.get("goal_reached"):
        L.append(_wrap("no score: the goal was not reached%s"
                       % (" yet" if out.get("end_reason") is None else "")
                       + (". The breakdown below is provisional - what you "
                          "would be optimising if you reached %s."
                          % (out.get("goal_in_words") or "the goal")
                          if out.get("end_reason") is None else "."),
                       indent=indent))
        L.append("")
    for name in _SCORE_COMPONENT_ORDER:
        c = (out.get("components") or {}).get(name)
        if not c:
            continue
        label = name.replace("_", " ")
        if c.get("normalized") is None:
            L.append("%s%-20s withheld: %s" % (indent, label, c.get("withheld", "-")))
            continue
        L.append("%s%-20s raw %-14s normalized %-6s weight %-5s weighted %s"
                 % (indent, label, _fmt_num(c.get("raw")),
                    "%.3f" % c["normalized"], "%.0f%%" % (c["weight"] * 100),
                    "%.4f" % c["weighted"]))
    L.append("")
    if out.get("total") is not None:
        L.append("%sTOTAL: %.1f%%  (%s / 1000 points)"
                 % (indent, out["total"] * 100, _fmt_num(out.get("points"))))
    else:
        L.append("%sTOTAL: -- (%s)" % (indent, out.get("no_score")
                 or "not computable until the run ends under fog"))
    ach = out.get("achievements") or {}
    if ach:
        L.append("")
        L.append("%sACHIEVEMENTS" % indent)
        for a in ach.values():
            L.append("%s  [%s] %s" % (indent, "x" if a["won"] else " ", a["what"]))
    return L
