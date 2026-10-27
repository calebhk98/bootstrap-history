"""Complaint 190, the wiring (the rules are test_coverage_rules and test_public_works_rules): how the game's coverage, disease burden,
roll-out, lit working day and schooling flow read the works, each method called on a stand-in `self` carrying only what it reads."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.diffusion import literacy_rules
from sim.diffusion.module import Diffusion
from sim.engine.forward_workforce import ForwardWorkforceMixin
from sim.refusal import cause_of
from sim.tests import module_harness, production_host, ventures_host
from sim.ui.proto.dispatch_rollout import _cmd_rollout
from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.workforce.constants import BASE_WORKING_DAY_HOURS
from sim.workforce.module import Workforce
from sim.tests.ui_stand_in import Game

CLINICS, LIGHTS = "ben_district_clinics", "ben_city_electric_lighting"


def works(open_units=0.0, is_open=True, known=True, nodes=(CLINICS,)):
    """The ventures module over a coverage work: 100 people to a unit, 1000 who can use it, `open_units` open."""
    opened = []
    module = ventures_host.build(
        tree_nodes={node: {"name": "Clinics"} for node in nodes}, running=lambda node_id: is_open,
        institution_units=lambda node_id: open_units, techniques_held={CLINICS} if known else set())
    module.people_per_unit = lambda node_id: 100.0
    module.people_who_can_use = lambda node_id: 1000.0
    module.coverage_nodes = lambda: list(nodes)
    module.open_venture = lambda node_id, units=None: opened.append((node_id, units)) or (True, "opened")
    return module, opened


# ---- coverage
game, _ = works(open_units=2.0)
check("an open work covers its units' people over those who can use it", abs(game.coverage_share(CLINICS) - 0.2) < 1e-12, None)
game, _ = works(open_units=2.0, is_open=False)
check("a shut work covers nothing", game.coverage_share(CLINICS) == 0.0, None)
game, _ = works()
check("the units that serve half the people are asked of the people and the unit's reach", game.units_for_coverage(CLINICS, 0.5) == 5.0, None)
check("the most units the nation can fill is the units that serve everyone",
      production_host.build(Game(coverage_nodes=lambda: [CLINICS], units_for_coverage=lambda node_id, share: 10.0 * share),
                             capability_sets=(set(), {CLINICS}, {})).institution_unit_ceiling(CLINICS) == 10.0, None)

# ---- the roll-out
game, opened = works()
ok, text = game.roll_out(CLINICS, 0.1)
check("rolling out a work not yet open opens it at the units the share needs", ok and opened == [(CLINICS, 1.0)], opened)
game, opened = works(open_units=3.0)
ok, text = game.roll_out(CLINICS, 0.1)
check("a share already covered opens nothing and says why", not ok and opened == [] and cause_of(text) == "already_covered", text)
game, opened = works(open_units=1.0)
game.roll_out(CLINICS, 0.5)
check("a work part open opens only what is still wanted", opened == [(CLINICS, 4.0)], opened)
game, opened = works(nodes=())
check("a work that cannot be rolled out is refused", game.roll_out(CLINICS, 0.5)[0] is False and opened == [], None)
game, opened = works(known=False)
check("a work not yet known is refused", game.roll_out(CLINICS, 0.5) == (False, "you have not worked out how to do that yet") and opened == [], None)

# ---- the rollout command
rolled = []
game = Game(coverage_nodes=lambda: [CLINICS], done={CLINICS}, coverage_row=lambda work: {"id": work},
                       roll_out=lambda node_id, share: rolled.append((node_id, share)) or (True, "opened"),
                       coverage_share=lambda node_id: 0.5, institution_units=lambda node_id: 5.0)
check("rollout with no work lists the works known", _cmd_rollout(game, {}, {}, None)["rollouts"] == [{"id": CLINICS}], None)
reply = _cmd_rollout(game, {}, {"id": CLINICS, "share": 50}, None)
check("rollout with a share above one is a percentage, and answers what it now covers", rolled == [(CLINICS, 0.5)] and reply["ok"] and reply["covered"] == 0.5
      and reply["units"] == 5.0, (rolled, reply))
check("rollout with a share beyond everyone is refused", _cmd_rollout(game, {}, {"id": CLINICS, "share": 150}, None)["ok"] is False, None)
check("rollout with a work and no share is refused", _cmd_rollout(game, {}, {"id": CLINICS}, None)["ok"] is False, None)

# ---- the lit working day
def lit_game(works_on, shares):
    return module_harness.build(Workforce, views={
        "mechanic": {"working_day": {node: {"extra_hours_per_day": 2.0} for node in works_on}},
        "running": lambda node_id: node_id in shares,
        "coverage": lambda: [node for node in works_on if node in shares and shares[node] is not None],
        "coverage_share": lambda node_id: shares[node_id]})


check("lights over half the people add half their lit hours", lit_game([LIGHTS], {LIGHTS: 0.5}).extra_lit_hours_per_day() == 1.0, None)
check("lights built but not open add nothing", lit_game([LIGHTS], {}).extra_lit_hours_per_day() == 0.0, None)
check("a lit work that declares no coverage lights the day for everyone", lit_game([LIGHTS], {LIGHTS: None}).extra_lit_hours_per_day() == 2.0, None)
check("with no work declaring a working day the year is the convention",
      lit_game([], {}).hours_per_person_year() == HOURS_PER_PERSON_YEAR, None)
check("a longer day gives a longer year in the same proportion",
      abs(lit_game([LIGHTS], {LIGHTS: 0.5}).hours_per_person_year()
          - HOURS_PER_PERSON_YEAR * (1.0 + 1.0 / BASE_WORKING_DAY_HOURS)) < 1e-9, None)
check("the year every wage quote reads is the working year", ForwardWorkforceMixin.HOURS_PER_PERSON_YEAR.fget(Game(view=lambda name: lambda: 1234.0)) == 1234.0, None)

# ---- the schooling flow
def schools(values, shut=(), reaches=None):
    terms = [(node_id, {"required": node_id in shut, "reaches": (reaches or {}).get(node_id)}) for node_id in values]
    return module_harness.build(Diffusion, views={"effect_terms": lambda channel: terms, "running": lambda node_id: node_id not in shut,
                                                  "effect_values": lambda channel: list(values.items())})


recorded = []
with mock.patch.object(literacy_rules, "schooling_flow", lambda schools_open, field, shut: recorded.append((schools_open, field, shut)) or 7.0):
    flow = schools({"school": 1.0, "village": 0.5}, reaches={"village": ["literacy_general"]}).schooling_flow("literacy_general")
check("the flow is the open schools with the fields each reaches, for the figure asked", flow == 7.0
      and recorded == [([(1.0, None), (0.5, ["literacy_general"])], "literacy_general", False)], recorded)
recorded.clear()
with mock.patch.object(literacy_rules, "schooling_flow", lambda schools_open, field, shut: recorded.append(shut) or 0.0):
    schools({"school": 1.0, "village": 0.5}, shut=("school",)).schooling_flow()
check("a required school that is shut is passed on as shut", recorded == [True], recorded)
