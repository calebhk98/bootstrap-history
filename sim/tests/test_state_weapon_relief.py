"""Complaint 330, part 2: the state's war relief has a per-weapon basis. Each military node the
government holds removes its own part of the harm, so the founder inventing more weapons never
lowers the relief and the state copying one more always raises it. Complaint 640: the relief is read off a stand-in
game that holds the founder's built nodes and the government's knowledge; no game is played."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.diffusion import constants
from sim.diffusion.diffusion_rules import weapons_relief
from sim.diffusion.module import Diffusion
from sim.engine import seat_builds
from sim.engine.hazard_relief import HazardReliefMixin
from sim.tests import module_harness

MILITARY = ["bronze_sword", "crossbow", "cannon", "rifle"]
KINDS = ("output_factor", "sack_chance")


class Armed(Diffusion):
    def diffusible_ids(self, category):
        return tuple(MILITARY) if category == "military" else ()


class Game(HazardReliefMixin):
    """Holds only what the relief reads: the founder's finished nodes, the government's knowledge, the military ids."""

    HAZARD_COUNTERS = {}
    STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = constants.STATE_MIL_RELIEF_PER_WEAPON_OUTPUT
    STATE_MIL_RELIEF_PER_WEAPON_SACK = constants.STATE_MIL_RELIEF_PER_WEAPON_SACK

    def __init__(self):
        self.built = set()
        self.held = set()
        self.state = SimpleNamespace(seats={"founder": SimpleNamespace(projects=SimpleNamespace(done=self.built, granted=set()))})
        self.diffusion = module_harness.build(Armed, views={
            "state_knowledge": lambda: self.held,
            "built_by_any_seat": lambda among: seat_builds.built_by_any(self.state.seats, among)})

    def _diffusible_ids(self, category):
        return self.diffusion.diffusible_ids(category)

    def state_military_diffusion(self):
        return self.diffusion.diffusion_index("military")

    def _state_military_diffusion_relief(self, per_weapon):
        return self.diffusion.diffusion_relief("military", per_weapon)

    def _military_war_relief(self):
        return 1.0, None


def relief(game):
    """The state's own armies' part of each kind of harm's multiplier."""
    return {kind: next((entry["factor"] for entry in game.hazard_relief_entries(kind) if entry["source"] == "state_weapons"), 1.0)
            for kind in KINDS}


# ---- the rule: each weapon removes its share of what is left ----------------------------------------
check("no weapon removes nothing and gives no reason", weapons_relief(0.04, 0) == (1.0, None))
one, many = weapons_relief(0.04, 1)[0], weapons_relief(0.04, 3)[0]
check("each weapon removes its share of what is left", abs(one - 0.96) < 1e-12 and abs(many - 0.96 ** 3) < 1e-12, (one, many))
gains = [weapons_relief(0.06, held)[0] - weapons_relief(0.06, held + 1)[0] for held in range(3)]
check("returns diminish: the next weapon removes less in absolute terms than the last", 0.0 < gains[2] < gains[1] < gains[0], gains)
check("no number of weapons removes all the harm", weapons_relief(0.06, 50)[0] > 0.0)

# ---- the relief follows the weapons the state holds --------------------------------------------------
game = Game()
game.built.add(MILITARY[0])
check("holding nothing gives no state relief of its own",
      all(entry["source"] != "state_weapons" for kind in KINDS for entry in game.hazard_relief_entries(kind)))
game.held.add(MILITARY[0])
one_held = relief(game)
check("one weapon held removes some harm of each kind", all(value < 1.0 for value in one_held.values()), one_held)
check("the relief per weapon is the declared one for each kind",
      abs(one_held["output_factor"] - (1.0 - game.STATE_MIL_RELIEF_PER_WEAPON_OUTPUT)) < 1e-12
      and abs(one_held["sack_chance"] - (1.0 - game.STATE_MIL_RELIEF_PER_WEAPON_SACK)) < 1e-12, one_held)

game.built.update(MILITARY[1:])
check("the founder inventing more weapons does not reduce the relief the state has", relief(game) == one_held, (one_held, relief(game)))
check("the share held falls while the relief does not", game.state_military_diffusion() < 1.0, game.state_military_diffusion())

game.held.add(MILITARY[1])
two_held = relief(game)
check("each further weapon the state holds removes more harm, of both kinds",
      all(two_held[kind] < one_held[kind] for kind in KINDS), (one_held, two_held))
game.held.add(MILITARY[2])
three_held = relief(game)
check("returns diminish in the game too: the next weapon removes less in absolute terms than the last",
      0.0 < two_held["sack_chance"] - three_held["sack_chance"] < one_held["sack_chance"] - two_held["sack_chance"],
      (one_held, two_held, three_held))
check("no number of weapons removes all the harm", all(value > 0.0 for value in three_held.values()))
game.held.add("a_weapon_nobody_built")
check("a weapon the founder never built counts for nothing", relief(game) == three_held)
