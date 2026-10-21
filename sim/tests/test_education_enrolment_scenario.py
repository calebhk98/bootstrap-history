"""Scenario: the `education` screen on a game. With schools running, their pupils made literate sum to the society's own
literacy gain, and the screen no longer says there is no per-school enrolment. The rules (shares, the literacy limit, the
column) are in test_education_enrolment."""
from .harness import *  # noqa: F401,F403


def _education(game):
    return S._agent_dispatch(game, NODES, {"cmd": "education"})


game = unopened_sim()
for node_id, spec in game._effect_terms("schooling_flow"):
    if node_id in NODES:
        game.done.add(node_id)
        game.operating.add(node_id)
game._done_changed()
reply = _education(game)
running = [row for row in reply["schools"] if row["flow_added"] > 0]
check("some school is running in the fixture", len(running) > 0, reply["schools"][:3])
population = game.population.total
gain = (reply["literacy"]["general_next_year"] - reply["literacy"]["general"]) * population
check("each school's pupils made literate next year are its share of the whole society's gain",
      abs(sum(row["people_made_literate_next_year"] for row in running) - gain) <= 1.0 + 0.01 * abs(gain),
      (gain, [row["people_made_literate_next_year"] for row in running]))
# presentation: the screen's note to the player must not deny the enrolment it now shows
check("not_held no longer says there is no per-school enrolment",
      not any("per-school enrolment" in line for line in reply["not_held"]), reply["not_held"])
