"""Complaint 640: the roster a game starts with is seeded once from the civilisation played and every economy trading
with it: the home country and each partner's country and government exist, with the partner's starting techniques.
The actors module over the real civilisation files, no game."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.module import Actors
from sim.agents.api import ActorsState, cast_from_civilisations
from sim.engine.data import load_civ

from .module_harness import build

PARTNERS = ["han_china_100ad", "norse_900ad"]


def game():
    opening = cast_from_civilisations(load_civ("rome_100ad"), [load_civ(partner) for partner in PARTNERS])
    module = build(Actors, views={"actor_kinds_registered": lambda: None, "opening_cast": lambda: opening}, world=ActorsState())
    return types.SimpleNamespace(actors=module.cast(), seed=module.seed_opening_cast)


class SeedOpeningCast(unittest.TestCase):
    def test_the_home_country_and_every_partner_and_its_government_are_seeded(self):
        sim = game()
        seeded = sim.seed()
        state = sim.actors.state
        self.assertTrue(seeded)
        self.assertEqual(state.home_country, "rome_100ad")
        self.assertTrue({"rome_100ad", *PARTNERS} <= set(state.countries))
        for partner in PARTNERS:
            government = sim.actors.get("government:" + partner)
            self.assertEqual(government.record.country, partner)
            self.assertEqual(state.countries[partner].starting_techs, set(load_civ(partner)["starting_techs"]))

    def test_it_seeds_once_and_the_saved_roster_stands_after(self):
        sim = game()
        sim.seed()
        cast, actors = dict(sim.actors.state.cast), set(sim.actors.actors)
        self.assertEqual(sim.seed(), [])
        self.assertEqual(dict(sim.actors.state.cast), cast)
        self.assertEqual(set(sim.actors.actors), actors)


if __name__ == "__main__":
    unittest.main()
