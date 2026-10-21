"""SCENARIO (Complaint 640): for Complaint 127: `start` warns when the free staff could not open the finished concern. The rule (a concern is
short when its need exceeds the free scholars or craftsmen, within a tolerance, and quiet when the free staff cover it) is
`staff_shortfall`, tested in test_completion_messaging; this is the reply through a whole game."""
from .harness import *  # noqa: F401,F403

WARNING = "today_you_could_not_open_this_when_it_is_done"

game = sim(capital=1_000_000)
game.done.update(NODES["school_founded"]["pre"])
game.done.add("freedman_staff")   # one option of the school's technical_staff group
game.venture_staff_free = lambda: (0.0, 0.0)
game.venture_hands = lambda node_id: (5.0, 5.0)

concern = S._agent_dispatch(game, NODES, {"cmd": "start", "id": "school_founded"})
check("a concern started with insufficient staff says so in the warning", bool(concern.get(WARNING)), concern.get(WARNING))
tech_game = sim(capital=1_000_000)
tech_game.venture_staff_free = lambda: (0.0, 0.0)
tech_game.venture_hands = lambda node_id: (5.0, 5.0)
plain_id = next((node_id for node_id in ORDER if not tech_game.is_venture(node_id) and tech_game.start_reason(node_id)[0]), None)
technology = S._agent_dispatch(tech_game, NODES, {"cmd": "start", "id": plain_id})
check("a non-concern technology that starts has no opening staff warning, with no free staff",
      plain_id is not None and technology.get("ok") and WARNING not in technology, (plain_id, technology))
