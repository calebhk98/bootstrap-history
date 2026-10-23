"""people_attrition_scholars: regression checks, run individually with `--only people_attrition_scholars`.

Staff are whole people; the scholar wall; the fog ratchet; the credit forecast and failure quote; the planner's
closure and ordering; typed-line spellings. The rules are called on the numbers and stand-ins each check states; the
agent loop's save before its reply and the start credit forecast are in test_agent_save_before_reply."""
import math
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

from sim.agents.household import Household
from sim.engine.economy_credit import CreditMixin
from sim.engine.mechanics import MechanicsMixin
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.engine.shortage_sizing import nitre_bed_yearly_spend
from sim.engine.society_adoption import AdoptionMixin
from sim.labour.labour_bondage import BondageMixin
from sim.labour.labour_capacity import CapacityMixin
from sim.labour.labour_training import TrainingMixin
from sim.labour.staff_pay_rules import roll_trade
from sim.labour.staff_targets import scholar_target
from sim.ui.proto import credit_forecast
from sim.world import demography

QUICK_TOPIC = True

# =============================================================================
# PEOPLE ARE WHOLE. Attrition is a per-person roll (`roll_trade`), so a headcount of whole people only ever loses
# whole people; hire() and train() refuse a fractional `n` outright.
# =============================================================================

DEATH_RATE = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
draws = random.Random(1)
headcount, whole_every_year, never_grew = 500, True, True
for _year in range(150):
    died, left, survivors = roll_trade(headcount, 0.0, DEATH_RATE, draws.random)
    whole_every_year = whole_every_year and isinstance(survivors, int) and survivors == headcount - died - left
    never_grew = never_grew and survivors <= headcount
    headcount = survivors
check("a whole headcount never picks up a fraction of a person, year after year of pure attrition",
      whole_every_year, headcount)
check("...and with nobody hiring the headcount only ever falls, never climbs on its own", never_grew, headcount)

# UNBIASED: the realised loss, averaged over many people and many independent seeds, should land on the working-age
# mortality rate (pay is at the market, so nobody takes a better offer).
lost = 0
for seed in range(1, 31):
    lost += roll_trade(2000, 0.0, DEATH_RATE, random.Random(seed).random)[0]
check("whole-person attrition averages the working-age mortality rate, over many people and many seeds",
      abs(lost / (30 * 2000.0) - DEATH_RATE) < 0.003, (lost / (30 * 2000.0), DEATH_RATE))

# HIRE AND TRAIN LAND WHOLE PEOPLE.
roster = SimpleNamespace(_world=SimpleNamespace(wages={"smith": 1.0, "machinist": 1.0}))
refused_hire = TrainingMixin.hire_check(roster, "smith", 2.5)[2]
refused_train = TrainingMixin.train_check(roster, "machinist", 1.5)[1]
check("hire refuses a fractional number of people", cause_of(refused_hire) == "count_not_whole", refused_hire)
check("...and so does train", cause_of(refused_train) == "count_not_whole", refused_train)
check("a whole number is not refused for being fractional",
      cause_of(TrainingMixin.train_check(roster, "machinist", 0)[1]) == "count_not_positive")

# =============================================================================
# THE SCHOLAR WALL. A literate trade's headcount ceiling is a floor plus the market's reach scaled by literacy; for
# scholars the institutions' own capacity is added; nobody can be hired who does not exist.
# =============================================================================


def wall_of(trade, institutional=0.0, literacy=1.0, exist=1e9, absent=()):
    stand_in = SimpleNamespace(
        LITERATE_TRADES=frozenset({"scholar", "scribe"}), LITERATE_CAPACITY_FLOOR=1.5, POP_SCALE_FLOOR_SHARE=0.5,
        POP_SCALE_VARIABLE_SHARE=0.5, SCHOLAR_MARKET_SHARE=0.35, local_market_share=lambda: 1.0,
        literacy_factor=lambda trade: literacy, staff_capacity=lambda: (institutional, 0.0, 0.0),
        people_who_exist=lambda trade: exist,
        _world=SimpleNamespace(cfg={"hired_hours_cap_base": 20_000.0}, pop_scale=1.0, HOURS_PER_PERSON_YEAR=2000.0,
                               trades_absent=set(absent)))
    return CapacityMixin.literate_capacity(stand_in, trade)


reach = 20_000.0 * 1.0 * (0.5 + 0.5) * 0.35 / 2000.0
check("the market-reach ceiling for a fresh household is the floor plus its reach scaled by literacy",
      abs(wall_of("scholar") - (1.5 + reach)) < 1e-9, wall_of("scholar"))
check("a trade that does not read has no literacy wall", wall_of("smith") == float("inf"))
check("a trade nobody can be found in cannot be had past the people who exist",
      wall_of("scribe", exist=2.0) == 2.0)
check("building the institutions that train scholars outright widens the wall by what they hold, for scholars alone",
      abs(wall_of("scholar", institutional=20.0) - wall_of("scholar") - 20.0) < 1e-9
      and wall_of("scribe", institutional=20.0) == wall_of("scribe"))
check("teaching the society to read widens the wall", wall_of("scribe", literacy=1.0) > wall_of("scribe", literacy=0.5))
wall_refusal = CapacityMixin._literate_wall_refusal(SimpleNamespace(), "scholar", 5.9, 0.0)
check("the refusal at the wall names the households' reach and literacy, and says how many can be taken",
      cause_of(wall_refusal) == "literacy_wall"
      and "reach" in str(wall_refusal) and "literacy" in str(wall_refusal)    # presentation: the refusal's wording
      and "5 more" in str(wall_refusal), wall_refusal)

# The same clamp auto_hire respects: a target already at the wall is capped at it.
check("auto_hire never asks for more scholars than the wall allows", scholar_target(10.0, 6.0, 0.5, 2.0) == 2.0)
check("...though it asks for more when the wall is open, so the check above measures the wall and not an unable household",
      scholar_target(10.0, 6.0, 0.5, 50.0) == 13.0)

# ONLY `scholar` COUNTS AS A TRAINED SCHOLAR, though the market groups scribes with them.
pools = SimpleNamespace(
    _world=SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(
        freedmen=0.0, slaves=0.0, training=[], granted_staff={"scholars": 1.0}, scholars=0.0, artisans=0.0))),
    employed_by_trade=lambda: {"scribe": 3.0, "scholar": 2.0, "smith": 4.0},
    is_craft_trade=lambda trade: trade == "smith", employed=lambda trade: {"scribe": 3.0, "scholar": 2.0}.get(trade, 0.0),
    WORKER_EQUIVALENT_UNTRAINED=1.0, FREEDMAN_ARTISAN_PRODUCTIVITY=1.0, TRAINED_SLAVE_ARTISAN_PRODUCTIVITY=1.0)
BondageMixin._resync_pools(pools)
household = pools._world.state.household
check("hiring scribes does not inflate the trained-scholar headcount; scholars and what an institution granted count",
      household.scholars == 2.0 + 1.0 and household.artisans == 4.0, (household.scholars, household.artisans))


class Advice(MechanicsMixin, AdoptionMixin):
    nodes = NODES


check("the advice on how to get scholars never points at a different trade family's trade, which would not even count",
      all("scribe" not in why and "chemist" not in why and "merchant" not in why and "engineer" not in why   # presentation: the authored wording of the advice
          for _node, why in Advice().STAFF_SOURCES.get("scholars", [])),
      Advice().STAFF_SOURCES.get("scholars"))

# --- SAVE INTEGRITY, JOB 2a: FOG CAN BE REWOUND. `revealed` is a ratchet: assigning to it may grow what this running
# session has seen, never shrink it.
projects = SimpleNamespace(revealed={"identity_cover", "workshop_first"})
ratchet = SimpleNamespace(_state=SimpleNamespace(projects=projects))
Household.revealed.fset(ratchet, {"identity_cover"})
check("fog cannot be rewound: assigning an earlier set keeps everything this session has already seen",
      projects.revealed == {"identity_cover", "workshop_first"}, sorted(projects.revealed))
Household.revealed.fset(ratchet, {"identity_cover", "metallurgy"})
check("...and assigning more grows it", projects.revealed == {"identity_cover", "workshop_first", "metallurgy"})
fresh = SimpleNamespace(_state=SimpleNamespace(projects=SimpleNamespace(revealed=None)))
Household.revealed.fset(fresh, {"identity_cover"})
check("a fresh resume still sees only what that save file actually recorded",
      fresh._state.projects.revealed == {"identity_cover"}, fresh._state.projects.revealed)

# planner.py works backward from the goal by critical-path method (CPM) over its prerequisite closure, instead of
# walking a hand-written list. These checks pin the structural properties the measured comparison depends on.
_p_s = SimpleNamespace(done=set(), granted=set(), _is_foreign_only=lambda node_id: False)
_p_order, _p_c, _p_extras, _p_staff = PLANNER.backward_plan(NODES, GOAL, _p_s, side_branches=0)
_p_need = S.closure(NODES, GOAL)
check("the planner's closure matches its own order's count for the goal",
      len(_p_need) == len(_p_order), (len(_p_need), len(_p_order)))
# closure() now follows the single-option req_any groups too - it also
# follows the `req_any` groups that have exactly one option (a mandatory
# dependency authored as a substitution rather than a `pre` edge; a group
# with two or more real alternatives is correctly left alone, both because
# only one is actually required and because counting every option can
# cycle). The gap is real and was the second thing this session's own audit
# found blocking the goal: `mat_bulk_steel` needs `mat_manganese` through
# exactly this kind of single-option `req_any`, `closure()` cannot see it on
# purpose, and a traced Rome run with 111 scholars, 428 artisans and 11.7
# million denarii in hand still had not built it by year 700 because it was
# never in `need` at all - staffing and money were both long since solved,
# ordering was not.
_pre_only = set()
_stk = [GOAL]
while _stk:
    _c = _stk.pop()
    if _c in _pre_only:
        continue
    _pre_only.add(_c)
    _stk.extend(NODES[_c]["pre"])
check("following `pre` alone understates what the goal needs by the "
      "req_any groups that are not really alternatives",
      _pre_only < _p_need and len(_p_need) > len(_pre_only),
      (len(_pre_only), len(_p_need)))
# --- THE DATA SAID OVERLAND IN THREE PLACES AND THE TREE SAID ROUND THE
# CAPE. mat_platinum_bulk's own note says the Ural placers are "reachable
# overland through Scythian and Sarmatian trade without crossing any ocean";
# geography.json lists platinum in siberia_urals as well as americas_south
# and repeats the sentence; and the node's only prerequisite was
# exp_africa_circumnavigation. Once closure() started following single-option
# req_any groups this stopped being a curiosity and became load-bearing:
# platinum is required for the glass-to-metal seal, so the goal's closure
# grew an entire age of exploration - six expedition nodes, the sextant, the
# compass, the lodestone, the cross-staff, the backstaff and a world map,
# seventeen nodes in all - to fetch a metal the data says is on a wagon road.

# --- THE ONE REMEDY THE GAME OFFERS, CAPPED AT THE HOUSEHOLD OF YEAR FIVE. Saltpetre has no market to buy from, so nitre
# beds are the whole answer; the automatic remedy lays a share of capital a year, held to a flat ceiling and never sized
# to the shortfall.
CEILING = 40_000.0
check("the nitre purchase is held to a flat yearly ceiling however rich the household",
      nitre_bed_yearly_spend(5_000_000.0, CEILING) == CEILING)
check("...and a poor household is held to a twentieth of its capital",
      abs(nitre_bed_yearly_spend(3_000.0, CEILING) - 3_000.0 * 0.05) < 1e-9)

# --- THREE PLAYERS, THREE CIVILISATIONS, THE SAME COMPLAINT: `start` financed the gap between what a project costs and
# what the household has, silently. Borrowing to build stays allowed; not being told was the bug.
forecast = credit_forecast.borrowing_forecast(
    instalments=1000.0, materials_paid_now=100.0, capital=400.0, credit_limit_of=lambda: 5000.0,
    interest_rate_of=lambda: 0.08, service_forecast_of=lambda owed: {"interest_per_year_at_that_draw": owed * 0.08})
check("starting a project you cannot cover in cash says you would be borrowing, what it costs a year, and how much room is left",
      forecast is not None and forecast["you_would_borrow"] == 600.0 and forecast["interest_rate_percent"] == 8.0
      and forecast["estimated_annual_interest"] == 48.0 and forecast["no_one_advances_past"] == 5000.0
      and forecast["you_would_then_owe"] == 600.0, forecast)
check("a household already in debt owes the gap on top of what it owes",
      credit_forecast.borrowing_forecast(1000.0, 0.0, -200.0, lambda: 5000.0, lambda: 0.08, lambda owed: {})
      ["you_would_then_owe"] == 1200.0)
check("a project you can pay for outright says nothing about credit",
      credit_forecast.borrowing_forecast(1000.0, 0.0, 1000.0, lambda: 1 / 0, lambda: 1 / 0, lambda owed: 1 / 0) is None)

# --- THE RATE WAS ON THE SCREEN AND THE SUM NEVER WAS. A failure takes a flat share of the money bill at risk: the total
# less the materials bought up front, which stay in stock.


def failure_stand_in(risk, cost_now, up_front, active=False):
    return SimpleNamespace(
        nodes={"work": {"risk": risk}}, FAILURE_RESET_SHARE=0.4, state=SimpleNamespace(projects=SimpleNamespace(
            active={"work": {}} if active else {})),
        project_cost=lambda node_id: cost_now, project_cost_now=lambda node_id: cost_now,
        _up_front_materials_money=lambda node_id: up_front)


stand_in = failure_stand_in(0.1, 1000.0, 300.0)
stand_in.failure_bill = lambda node_id: ProjectMaterialsMixin.failure_bill(stand_in, node_id)
loss = ProjectMaterialsMixin.failure_loss(stand_in, "work")
check("a failure costs the reset share of the money bill at risk, which is never more than that share of the total",
      abs(loss - 0.4 * (1000.0 - 300.0)) < 1e-9 and loss <= 0.4 * 1000.0, loss)
check("...and a work that cannot fail is not given an imaginary danger",
      ProjectMaterialsMixin.failure_loss(failure_stand_in(0, 1000.0, 300.0), "work") == 0.0)

# --- DEVELOPER MARKERS IN PLAYER PROSE, THE SECOND TIME. A strip pass removed
# 1,108 `[AUDIT: ...]` markers from node notes after a first-time tester found
# one in the win condition itself. It matched that one phrase, and 22 nodes
# carried a DIFFERENT one - "[FIXED after independent audit: ...]" - which an
# outside player then found in a furnace description and reported as
# immersion-breaking. The markers are worth keeping; `note` is not where they
# belong. `_internal` is read by nothing in sim/engine.
#
# This check is deliberately about the SHAPE rather than a list of phrases,
# because the thing that failed twice was a phrase list.
_BRACKETED = __import__("re").compile(r"\[[^\]]{0,400}\]")
_DEV_WORDS = ("audit", "fixed after", "todo", "fixme", "xxx", "see job",
              "provenance", "heuristic", "my own", "treat as a floor")
_leaks = []
for _k, _n in sorted(NODES.items()):
    for _m in _BRACKETED.findall(_n.get("note") or ""):
        if any(word in _m.lower() for word in _DEV_WORDS):
            _leaks.append((_k, _m[:70]))
check("no node's player-facing note carries a bracketed developer aside - "
      "an outside player found '[FIXED after independent audit: ...]' in a "
      "furnace description after the first strip pass missed that phrase",
      _leaks == [], _leaks[:4])
check("nothing in the engine reads _internal, which is what makes it safe "
      "to keep developer notes there",
      not any("_internal" in open(os.path.join(HERE, filename)).read()
              for filename in ("engine/core.py", "engine/economy.py", "engine/projects.py", "labour/labour.py",
                         "engine/society.py", "ui/protocol.py", "ui/cli.py", "engine/fog.py",
                         "engine/data.py")),
      "engine files mentioning _internal")

# --- THE SAME HOLE IN A SECOND COMMAND. `available`'s parser read bare words
# only, so `available all:true` - the spelling `help commands` itself gives -
# fell through to the subject branch and was used as a search string named
# "all:true", matching nothing, silently. The same hole swallowed limit:30,
# find:furnace and every other pair. `state full:true` has always taken this
# spelling, so a player who learned it there was right to expect it.
for _av, _want in (("available all", {"cmd": "available", "all": True}),
                   ("available all:true", {"cmd": "available", "all": True}),
                   ("available limit:30 offset:30",
                    {"cmd": "available", "limit": 30, "offset": 30}),
                   ("available find:furnace",
                    {"cmd": "available", "find": "furnace"})):
    check("'%s' is understood" % _av, _PT(_av)[0] == _want, _PT(_av)[0])
check("a bare subject is still a subject, not mistaken for a flag",
      _PT("available metallurgy")[0] == {"cmd": "available",
                                         "subject": "metallurgy"},
      _PT("available metallurgy")[0])

# --- THE HELP ADVERTISED A SPELLING THE PARSER DID NOT ACCEPT, and the
# failure was silent and expensive. `rush`'s own help says "add limit:N to
# cap it"; `limit:3` is not a number, so the token scan came back empty, no
# limit was set, and rush went on to begin everything startable. A Norse
# player who read the help, wanted three things, and typed exactly what they
# were told got twenty-one projects and every denarius of their credit. The
# safest-looking spelling of the most expensive command in the game was the
# one that removed the safety.
for _sp in ("rush 3", "rush limit:3", "rush limit 3", "rush limit=3"):
    check("'%s' caps the rush at three" % _sp,
          _PT(_sp)[0] == {"cmd": "rush", "limit": 3},
          _PT(_sp)[0])
check("a cap that does not parse is refused, not shrugged off into "
      "starting everything - the one typo a careful player can make must "
      "not be the typo that begins the whole tree",
      _PT("rush limit:abc")[0] is None
      and cause_of(_PT("rush limit:abc")[1]) == "cap_not_a_number",
      _PT("rush limit:abc"))
check("platinum is reachable the way its own note and the geography file "
      "both say it is, overland, without rounding the Cape",
      "exp_africa_circumnavigation" not in S.closure(NODES, "mat_platinum_bulk"),
      sorted(node_id for node_id in S.closure(NODES, "mat_platinum_bulk")
             if node_id.startswith("exp_")))
check("...and the goal no longer requires an age of exploration to reach a "
      "transistor: one trade route, not six voyages",
      sorted(node_id for node_id in S.closure(NODES, GOAL) if node_id.startswith("exp_"))
      == ["exp_trade_route_extend"],
      sorted(node_id for node_id in S.closure(NODES, GOAL) if node_id.startswith("exp_")))
GEO_MATS = [place["name"] for place in S.load_geography()["located_materials"]["platinum"]["places"]]
check("the Colombian placers are still a route, just not the only one",
      any("Colombia" in name for name in GEO_MATS) and any("Urals" in name for name in GEO_MATS),
      GEO_MATS)
check("mat_bulk_steel (on the critical path) is gated on mat_manganese "
      "through exactly one req_any option, no real alternative offered",
      NODES["mat_bulk_steel"]["req_any"] ==
      [{"group": "manganese_supply", "options": {"mat_manganese": 1.0}}],
      NODES["mat_bulk_steel"]["req_any"])
check("closure() catches it now: mat_manganese and its own "
      "prerequisite mat_pyrolusite are both required, where a pre-only "
      "walk leaves both out",
      {"mat_manganese", "mat_pyrolusite"} <= _p_need
      and not ({"mat_manganese", "mat_pyrolusite"} & _pre_only),
      (sorted({"mat_manganese", "mat_pyrolusite"} & _p_need),
       sorted({"mat_manganese", "mat_pyrolusite"} & _pre_only)))
# ONE DEFINITION OF A HARD EDGE, or the ordering schedules a requirement too
# late. closure() learned the single-option groups first and topo_order and
# critical_path did not, so mat_manganese was correctly called required and
# then sorted AFTER the mat_bulk_steel that requires it. All three read
# hard_pre() now.
check("the order the ENGINE receives puts the single-option dependency "
      "first - topo_stable in cli.py was the last place still reading `pre` "
      "alone, and brought mat_manganese out at 187 behind the "
      "mat_bulk_steel at 65 that cannot be built without it",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          PLANNER._repaired(NODES, GOAL, _p_order)),
      "engine-order manganese/bulk steel")
check("topo_order puts a single-option req_any dependency before the node "
      "that requires it, not after",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          S.topo_order(NODES, _p_need)),
      "mat_manganese/mat_bulk_steel ordering")
check("hard_pre never repeats an id, however a node names it - a "
      "duplicate inflates topo_order's in-degree past what the decrement "
      "can undo, and reports ten blameless nodes as a cycle",
      all(len(S.hard_pre(NODES, node_id)) == len(set(S.hard_pre(NODES, node_id)))
          for node_id in NODES),
      [node_id for node_id in sorted(NODES)
       if len(S.hard_pre(NODES, node_id)) != len(set(S.hard_pre(NODES, node_id)))][:5])
_syn_req = {
    "goal2":  {"pre": ["mandatory"], "req_any": [], "yrs": 0, "ph": 0, "_total_cost": 0},
    "mandatory": {"pre": [], "req_any": [{"group": "g1", "options": {"onlyroute": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 10},
    "onlyroute": {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "choice":    {"pre": [], "req_any": [{"group": "g2", "options": {"routeA": 1.0, "routeB": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeA":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeB":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
}
check("a single-option req_any group's target is pulled into "
      "closure() - the mandatory-dependency-in-disguise case",
      "onlyroute" in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
_syn_req["goal2"]["pre"] = ["choice"]
check("a genuine req_any CHOICE is left alone - neither option of a "
      "two-way alternative is forced into the closure",
      "routeA" not in S.closure(_syn_req, "goal2")
      and "routeB" not in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
# The acyclic check against the WHOLE real tree (not just this synthetic
# pair) needs `_cycle_on`, defined later in this file - see the check next
# to "the tree is acyclic on hard prerequisites" below.
# THE STAFFING LAYER, which is the one thing in a plan that the tech tree
# cannot supply. A node's prerequisites are other nodes; its demand for
# "eight trained scholars" is a demand on the household, and no amount of
# ordering the closure correctly satisfies it. Both civilisations' plans used
# to run out of horizon with quantum_solidstate_theory as the first blocked
# node - the cheapest node in the late programme, wanting eight scholars
# against a society whose lettered pool tops out at 5.9.
check("the planner names the institutions that train people, which the "
      "goal's own prerequisite closure never mentions",
      _p_staff and all(node_id not in _p_need for node_id in _p_staff)
      and "school_founded" in _p_staff and "academy_network" in _p_staff,
      _p_staff)
check("...and does not order them, which was measured and made Rome's run "
      "three centuries worse - 278,000 denarii of founding cost and "
      "perpetual upkeep against a household that starts with four hundred",
      all(node_id not in _p_order for node_id in _p_staff),
      [node_id for node_id in _p_staff if node_id in _p_order])
from sim.engine.mechanics import staff_capacity_sources
_staff_sources = staff_capacity_sources(NODES)
check("the staffing list is read from the same table staff_capacity() "
      "itself iterates, so the two cannot drift apart",
      all(node_id in {entry[0] for entry in _staff_sources} for node_id in _p_staff),
      sorted(_p_staff))
check("every node staff_capacity() credits actually exists in the tree - "
      "bessemer_openhearth did not, so its sixty-five artisans were never "
      "once handed over",
      [entry[0] for entry in _staff_sources if entry[0] not in NODES] == [],
      [entry[0] for entry in _staff_sources if entry[0] not in NODES])
_p_zero = [node_id for node_id in _p_need if _p_c["slack"][node_id] <= 1e-6]
_p_pos = {node_id: i for i, node_id in enumerate(_p_order)}
check("every zero-slack (critical-path) node is ordered before every node "
      "that has room to wait",
      max(_p_pos[node_id] for node_id in _p_zero) < min(_p_pos[node_id] for node_id in _p_need
                                            if _p_c["slack"][node_id] > 1e-6),
      "critical nodes occupy positions 0-%d of %d" % (len(_p_zero) - 1, len(_p_order)))
check("the critical-path total the planner computes matches `validate`'s "
      "142-year figure for this tree",
      abs(_p_c["total"] - S.critical_path(NODES, GOAL)[0]) < 1e-6,
      (_p_c["total"], S.critical_path(NODES, GOAL)[0]))
# A strategy file this module writes must reach the engine with no node ever
# asked to start before its own prerequisite - the thing `load_strategy`'s
# own `topo_stable` exists to guarantee for ANY strategy file, not only this
# one, but the planner's raw CPM order is exactly the case that needs it:
# slack is not monotonic along an edge (see the comment in planner.py), so
# the unrepaired order has real violations, and this checks the repair that
# reaches the engine removes every one of them.
_p_side_branches = PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12)
os.makedirs(os.path.join(ROOT, _PLAY_DIR), exist_ok=True)
_p_path = os.path.join(ROOT, _PLAY_DIR, "planned_check.json")
PLANNER.write_strategy(_p_path, "test", [], PLANNER.interleave(
    _p_order, _p_side_branches, 8))
_p_label, _p_full, _p_bounties = S.load_strategy(_p_path, NODES, GOAL)
_p_fullpos = {node_id: i for i, node_id in enumerate(_p_full)}
_p_violations = [(prereq_id, node_id) for node_id in _p_need for prereq_id in NODES[node_id]["pre"]
                 if prereq_id in _p_need and _p_fullpos.get(prereq_id, -1) > _p_fullpos.get(node_id, 10 ** 9)]
check("a plan this module writes never asks the engine to start something "
      "before its own prerequisite, once loaded the same way --strategy loads it",
      not _p_violations, _p_violations[:5])
check("the side branches a plan weaves in are all revenue-positive and none "
      "is a technical prerequisite of the goal",
      _p_extras is not None and all(
          node_id not in _p_need and NODES[node_id]["rev"] > NODES[node_id]["up"]
          for node_id in _p_side_branches),
      _p_side_branches[:5])

# A SEED IMPROVES TIES, IT DOES NOT OVERRIDE THE GRAPH. Proven on a tiny
# synthetic DAG rather than the real tree, because the real tree (checked
# directly) has no two unrelated nodes with identical slack AND identical
# earliest-start - the tie-break is real but the live data never exercises it,
# which is exactly the gap a synthetic case is for.
_syn = {
    "goal": {"pre": ["a", "b"], "yrs": 0, "ph": 0, "_total_cost": 0},
    "a":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
    "b":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
}
_syn_order1, _c1, _e1, _s1 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["b", "a"],
                                              side_branches=0)
_syn_order2, _c2, _e2, _s2 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["a", "b"],
                                              side_branches=0)
check("(setup) the synthetic pair is a genuine tie: equal slack and equal "
      "earliest start, with no dependency between them",
      _c1["slack"]["a"] == _c1["slack"]["b"] and _c1["es"]["a"] == _c1["es"]["b"],
      (_c1["slack"], _c1["es"]))
check("a seed order breaks a tie the critical path itself cannot call, "
      "without needing to change when the seed agrees with the default",
      _syn_order1.index("b") < _syn_order1.index("a")
      and _syn_order2.index("a") < _syn_order2.index("b"),
      (_syn_order1, _syn_order2))

# --- refine() MUST MEASURE WHAT --strategy ACTUALLY LOADS, not its own raw,
# unrepaired ~161-node order. The first version of refine() handed
# `cur_order` straight to `Sim()`, skipping the `topo_stable` repair
# `load_strategy` always applies - and since the raw CPM order has 132 real
# topological violations (see the comment after `cpm` in planner.py), that
# silently measured a different, broken order: a live check of one refine
# round went from 0/3 trials reaching the goal to 3/3 the moment this was
# fixed, against the IDENTICAL seeds and the identical starting order. This
# pins the fix: `_repaired` must agree with what `load_strategy` returns for
# the same order.
_p_repaired = PLANNER._repaired(NODES, GOAL, _p_order)
_p_label2, _p_expected, _p_b2 = S.load_strategy(
    PLANNER.write_strategy(os.path.join(ROOT, _PLAY_DIR, "refine_check.json"),
                           "test", [], _p_order),
    NODES, GOAL)
check("refine() measures a candidate order the same way --strategy loads it "
      "(full tree, topo_stable-repaired), not its own raw closure-only list",
      _p_repaired == _p_expected, (len(_p_repaired), len(_p_expected)))
