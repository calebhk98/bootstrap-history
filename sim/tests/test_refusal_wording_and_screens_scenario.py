"""The policy screen's claim that `auto_open` is merely off, through a running game: with the policy on,
auto_open_ventures takes one of the concerns that clear the most a year for what they cost to open, and the policy was
off by default. The refusal wording and the screens are test_refusal_wording_and_screens."""
from .harness import *  # noqa: F401,F403

game = unopened_sim(civ="england_1300")
# the concerns the household's free hands can staff (the gate `open` applies) that clear the most a year for the money
# to open them; their takings come from what they make
pays_best = sorted((node_id for node_id, node in game.nodes.items()
                    if node["rev"] > node["up"] and game.is_venture(node_id)
                    and game.staffing_open_refusal(node_id) is None),
                   key=lambda node_id: -(game.nodes[node_id]["rev"] - game.nodes[node_id]["up"])
                   / max(1.0, game.venture_capex(node_id)))[:5]
check("auto_open is off by default", game.policy.get("auto_open") is False, game.policy)
game.done.update(pays_best)
game._done_changed()
opened = game.auto_open_ventures()
check("auto_open really would open a concern that plainly pays for itself: of the five that clear the most a year "
      "against what they cost to open, auto_open_ventures takes one",
      any(node_id in opened for node_id in pays_best), (pays_best, opened))
