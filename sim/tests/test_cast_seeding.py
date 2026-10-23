"""Complaint 640: the roster a game starts with is seeded once from the civilisation played and every economy trading
with it: the home country and each partner's country and government exist, with the partner's starting techniques.
Over a stand-in with the real civilisation files, no game."""
QUICK_TOPIC = True

import types
import unittest

from sim.agents.api import ActorRegistry, ActorsState
from sim.engine.agents_port_cast import seed_opening_cast
from sim.engine.data import load_civ

PARTNERS = ["han_china_100ad", "norse_900ad"]


def game():
    return types.SimpleNamespace(actors=ActorRegistry(ActorsState()), start_civ=load_civ("rome_100ad"),
                                 partner_countries=lambda: list(PARTNERS))


class SeedOpeningCast(unittest.TestCase):
    def test_the_home_country_and_every_partner_and_its_government_are_seeded(self):
        sim = game()
        seeded = seed_opening_cast(sim)
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
        seed_opening_cast(sim)
        cast, actors = dict(sim.actors.state.cast), set(sim.actors.actors)
        self.assertEqual(seed_opening_cast(sim), [])
        self.assertEqual(dict(sim.actors.state.cast), cast)
        self.assertEqual(set(sim.actors.actors), actors)


if __name__ == "__main__":
    unittest.main()
