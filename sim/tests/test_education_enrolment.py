"""education_enrolment: regression checks, run with `--only education_enrolment`."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_typed import render_pretty as _render_pretty


def _education(game):
    return S._agent_dispatch(game, NODES, {"cmd": "education"})


none_running = sim()
reply = _education(none_running)
check("with no school running, literacy is limited by the missing schools",
      reply["literacy_limited_by"] == "no school running", reply.get("literacy_limited_by"))

game = sim()
for node_id, spec in game._effect_terms("schooling_flow"):
    if node_id in NODES:
        game.done.add(node_id)
        game.operating.add(node_id)
game._done_changed()
reply = _education(game)
running = [row for row in reply["schools"] if row["flow_added"] > 0]
check("some school is running in the fixture", len(running) > 0, reply["schools"][:3])
_total = sum(row["flow_added"] for row in running)
check("each running school shows its share of the schooling flow, summing to one",
      abs(sum(row["share_of_schooling_flow"] for row in running) - 1.0) < 0.01
      and all(abs(row["share_of_schooling_flow"] - row["flow_added"] / _total) < 0.001 for row in running),
      running[:3])
population = game.population.total
gain = (reply["literacy"]["general_next_year"] - reply["literacy"]["general"]) * population
check("each school's pupils made literate next year are its share of the whole society's gain",
      abs(sum(row["people_made_literate_next_year"] for row in running) - gain) <= 1.0 + 0.01 * abs(gain),
      (gain, [row["people_made_literate_next_year"] for row in running]))
check("the screen prints the enrolment column",
      "PUPILS" in _render_pretty("education", reply).upper(), _render_pretty("education", reply)[:600])
check("not_held no longer says there is no per-school enrolment",
      not any("per-school enrolment" in line for line in reply["not_held"]), reply["not_held"])
