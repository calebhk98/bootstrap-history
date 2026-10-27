"""step_problems: the end-of-step problem list, the risk screen's confiscation block, lapsed-hedge naming. Complaint 640:
each rule is called on a stand-in game or a reply built here; no game is played."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.tests import hazards_host, polity_host
from sim.polity import constants as polity_constants
from sim.ui.proto import render_screen_step as _render_big
from sim.ui.proto.dispatch_inspection_society import _cmd_risk
from sim.ui.proto.render_screens_status import render_risk, render_score
from sim.ui.proto.score_total import score_total
from sim.ui.proto.step_problems import step_problems, problems_lines, route_nodes, route_startable
from sim.tests.ui_stand_in import Game

events = [{"year": 101, "message": "interest on 330 denarii of arrears at 10.9% a year", "event_kind": "arrears_interest"},
          {"year": 102, "message": "CREDIT EXHAUSTED: 3 projects stopped", "event_kind": "credit_exhausted"},
          {"year": 103, "message": "THE TREASURY IS LOOKING AT YOUR FORTUNE: a 5% chance", "event_kind": "treasury_watching"},
          {"year": 103, "message": "Antonine plague: staff -10%", "event_kind": "hazard_hit",
           "facts": {"lapsed_hedges": ["Sand filter"]}}]
snapshots = [{"year": 101, "route_startable": False, "concerns_closed": ["a"]},
             {"year": 102, "route_startable": False, "concerns_closed": ["b", "c"]},
             {"year": 103, "route_startable": True, "concerns_closed": []}]
problems = step_problems(3, snapshots, events, ["Aqueduct"])
joined = " | ".join(problems)
check("problems name the stalled route, credit, closures, treasury, lapsed hedge and stalled projects",  # presentation: the problem wording
      "2 of 3 years" in joined and "credit exhausted" in joined and "3 concerns closed" in joined
      and "treasury" in joined and "Sand filter" in joined and "Aqueduct" in joined, problems)
check("a single-year step has no problem list", step_problems(1, snapshots, events, []) == [])
check("a quiet multi-year step has no problem list", step_problems(3, [{"year": 1}], [], []) == [])
rendered = _render_big.render_step(dict(ok=True, completed=[], events=[], lost=[], year=103, problems=problems))
check("the step screen ends with the problems block, then the one pointer line",  # presentation: layout of the step screen
      rendered.splitlines()[-len(problems_lines(problems)) - 2:-2] == problems_lines(problems)
      and rendered.splitlines()[-1] == 'Type "state full" for the full list.', rendered[-300:])

# ---- the goal route and whether anything on it can be begun -------------------------------------------------
nodes = {"goal": {"pre": ["middle"]}, "middle": {"pre": ["root"]}, "root": {"pre": []}, "side": {"pre": []}}
route_game = Game(goal="goal", nodes=nodes, done=set(), active={}, can_start=lambda node_id: node_id == "root")
route = route_nodes(route_game)
check("the goal route is the goal and everything it needs, and nothing beside it", route == {"goal", "middle", "root"}, route)
check("a route with a startable step is startable", route_startable(route_game, route) is True)
route_game.can_start = lambda node_id: False
check("a route with nothing startable is not", route_startable(route_game, route) is False)
route_game.done = set(route)
check("a finished route has nothing to start", route_startable(route_game, route) is None)
check("a game with no goal has no route", route_nodes(Game(goal=None, nodes=nodes)) == set())


# ---- a lapsed hedge names the concern whose closure lapsed it ----------------------------------------------
class HedgeGame:
    """The hazards module with one sanitation hedge built, running or shut."""

    def __init__(self, running):
        self.module = hazards_host.build(
            hazard_counter_rows={"staff_loss": [(0, "sanitation_antisepsis", 0.5, "Sand filter")]},
            tree=lambda node: {"name": "Antiseptic sanitation"}, techniques_held={"sanitation_antisepsis"},
            running=lambda node: running)

    def hazard_relief_detail(self, kind):
        return self.module.hazard_relief_detail(kind)


_multiplier, _why, lapsed_names = HedgeGame(False).hazard_relief_detail("staff_loss")
check("a lapsed hedge names the concern whose closure lapsed it", lapsed_names == ["Antiseptic sanitation"], lapsed_names)
running = HedgeGame(True).hazard_relief_detail("staff_loss")
check("a hedge that is running lapses nothing and takes its full share off", running[2] == [] and abs(running[0] - 0.5) < 1e-12, running)

# ---- the risk reply carries the confiscation block ----------------------------------------------------------
LABELS = polity_constants.CONFISCATION_PROTECTION_LABELS


def pressure_module():
    module = polity_host.build()
    module.confiscation_risk = lambda: (0.123456, [LABELS[0]])
    return module


status = pressure_module().confiscation_status()
check("the confiscation status gives the chance, what holds it off and what is not yet in force",
      status == {"chance_this_year": 0.1235, "held_off_by": [LABELS[0]], "not_yet_in_force": list(LABELS[1:])}, status)
risk_game = Game(knowledge_risk=lambda: {}, year=100, confiscation_status=lambda: status, interest_groups=lambda: [])
risk_reply = _cmd_risk(risk_game, {}, {"cmd": "risk"}, None)
check("risk reply carries the confiscation block", risk_reply["confiscation"] == status, sorted(risk_reply))
risk_text = render_risk(risk_reply)
check("the risk screen shows the confiscation chance and its protections",  # presentation: the screen's wording
      "TREASURY CONFISCATION" in risk_text and "held off by" in risk_text and "a patron" in risk_text, risk_text[-400:])

# ---- the score total ------------------------------------------------------------------------------------------
components = {name: {"normalized": 0.5, "weighted": weight} for name, weight in (("a", 0.25), ("b", 0.25), ("c", 0.5))}
check("a total is the sum of the weighted components, and a thousand points is a perfect run",
      score_total(components) == (1.0, 1000), score_total(components))
check("a rounded total is rounded as points", score_total({"a": {"normalized": 0.1, "weighted": 0.12345}}) == (0.1235, 124))
components["c"]["normalized"] = None
check("a total is withheld while any component is withheld", score_total(components) == (None, None))
report = {"goal_reached": False, "goal_in_words": "the printing press", "end_reason": "the horizon",
          "components": {name: dict(value, raw=1.0, weight=value["weighted"] * 2.0) for name, value in
                         {"technology_coverage": {"normalized": 0.4, "weighted": 0.1}}.items()},
          "total": 0.1, "points": 100, "achievements": {}}
score_text = render_score(report)
check("score shows a total flagged goal not reached",  # presentation: the score screen's wording
      "TOTAL: 10.0%" in score_text and "goal not reached" in score_text, score_text[-300:])
withheld = render_score(dict(report, total=None, points=None))
check("a withheld total is shown as withheld, not as a number",  # presentation: the score screen's wording
      "TOTAL: --" in withheld and "TOTAL: 10.0%" not in withheld, withheld[-300:])
