"""step_problems: the end-of-step problem list, the risk screen's confiscation block, lapsed-hedge naming."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto import render_screens_big as _render_big
from sim.engine.proto.render_screens_status import render_risk
from sim.engine.proto.step_problems import step_problems, problems_lines, route_nodes, route_startable

events = [{"year": 101, "message": "interest on 330 denarii of arrears at 10.9% a year"},
          {"year": 102, "message": "CREDIT EXHAUSTED: 3 projects stopped"},
          {"year": 103, "message": "THE TREASURY IS LOOKING AT YOUR FORTUNE: a 5% chance"},
          {"year": 103, "message": "Antonine plague: staff -10% (softened by clean water (lapsed: Sand filter is closed))"}]
snapshots = [{"year": 101, "route_startable": False, "concerns_closed": ["a"]},
             {"year": 102, "route_startable": False, "concerns_closed": ["b", "c"]},
             {"year": 103, "route_startable": True, "concerns_closed": []}]
problems = step_problems(3, snapshots, events, ["Aqueduct"])
joined = " | ".join(problems)
check("problems name the stalled route, credit, closures, treasury, lapsed hedge and stalled projects",
      "2 of 3 years" in joined and "credit exhausted" in joined and "3 concerns closed" in joined
      and "treasury" in joined and "Sand filter" in joined and "Aqueduct" in joined, problems)
check("a single-year step has no problem list", step_problems(1, snapshots, events, []) == [])
check("a quiet multi-year step has no problem list", step_problems(3, [{"year": 1}], [], []) == [])
rendered = _render_big.render_step(dict(ok=True, completed=[], events=[], lost=[], year=103, problems=problems))
check("the step screen ends with the problems block",
      rendered.splitlines()[-len(problems_lines(problems)):] == problems_lines(problems), rendered[-300:])

test_sim = sim()
route = route_nodes(test_sim)
check("the goal route is found and startability is a boolean",
      route and isinstance(route_startable(test_sim, route), bool), len(route))

hedge_sim = sim()
hedge_sim.done.add("sanitation_antisepsis")
hedge_sim._done_changed()
_multiplier, why = hedge_sim.hazard_relief("staff_loss")
check("a lapsed hedge names the concern whose closure lapsed it",
      any("lapsed: " in text and text.endswith("is closed)")
          and hedge_sim.nodes["sanitation_antisepsis"]["name"] in text for text in why), why)

risk_replies, _, _ = proto([{"cmd": "risk"}])
check("risk reply carries the confiscation block",
      "confiscation" in risk_replies[0] and "chance_this_year" in risk_replies[0]["confiscation"],
      sorted(risk_replies[0]))
risk_text = render_risk(risk_replies[0])
check("the risk screen shows the confiscation chance and its protections",
      "TREASURY CONFISCATION" in risk_text and "held off by" in risk_text, risk_text[-400:])

score_sim = sim()
score_sim.year = score_sim.cfg["start_year"] + score_sim.cfg["horizon_years"]
from sim.engine.protocol import score_report, render_score
score_text = render_score(score_report(score_sim, NODES))
check("score shows a total flagged goal not reached",
      "TOTAL: " in score_text and "TOTAL: --" not in score_text and "goal not reached" in score_text, score_text[-300:])
