"""Complaint 330, part 2: the state's war relief has a per-weapon basis. Each military node the
government holds removes its own part of the harm, so the founder inventing more weapons never
lowers the relief and the state copying one more always raises it."""
from .harness import *  # noqa: F401,F403

military = sorted(node_id for node_id, node in NODES.items()
                  if "military" in (node.get("traits") or ()) and node_id != "patron_imperial")[:4]
game = sim(civ="rome_100ad")
run_it(game, "patron_imperial")
government = game.state_treasury()


def invent(node_id):
	game.done.add(node_id)
	game.done_year[node_id] = game.year - 200


def relief():
	"""The state's own armies' part of each kind of harm's multiplier (the founder's private
	defences are a separate entry and change as the founder builds)."""
	return {kind: next((entry["factor"] for entry in game.hazard_relief_entries(kind)
	                    if "state's own armies" in entry["label"]), 1.0)
	        for kind in ("output_factor", "sack_chance")}


invent(military[0])
check("holding nothing gives no state relief of its own",
      all("state's own armies" not in line for kind in ("output_factor", "sack_chance")
          for line in game.hazard_relief(kind)[1]))
government.knowledge.add(military[0])
one_held = relief()
check("one weapon held removes some harm of each kind", all(value < 1.0 for value in one_held.values()), one_held)

for node_id in military[1:]:
	invent(node_id)
check("the founder inventing more weapons does not reduce the relief the state has",
      relief() == one_held, (one_held, relief()))
check("the share held falls while the relief does not", game.state_military_diffusion() < 1.0)

government.knowledge.add(military[1])
two_held = relief()
check("each further weapon the state holds removes more harm, of both kinds",
      all(two_held[kind] < one_held[kind] for kind in one_held), (one_held, two_held))
gain_second = one_held["sack_chance"] - two_held["sack_chance"]
government.knowledge.add(military[2])
three_held = relief()
gain_third = two_held["sack_chance"] - three_held["sack_chance"]
check("returns diminish: the next weapon removes less in absolute terms than the last",
      0.0 < gain_third < gain_second, (gain_second, gain_third))
check("no number of weapons removes all the harm", all(value > 0.0 for value in three_held.values()))
