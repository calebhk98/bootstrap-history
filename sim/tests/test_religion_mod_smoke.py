"""SMOKE: the Religion code mod in a whole game with the agent economy open, allowed in a temporary mods directory. The mod adds an actor
kind; the civilisation variant that starts with a temple estate gets an actor of that kind, which collects rent and spends part of
its surplus on land through the ordinary ledger, so after two years its purse and its endowment have grown from the start values the
variant's cast entry sets. The mod imports only the mod door."""
import unittest

from sim.tests.shipped_mod_games import ModGames

MOD = "bh_religion_h5p1"
VARIANT = MOD + ":rome_temple_estates"
KIND = MOD + ":religious_house"
HOUSE = "houses:home"


class ReligionModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD])
        cls.game = cls.games.opened(civ=VARIANT)
        house = cls.game.view("cast")().actors[HOUSE]
        cls.start_money, cls.start_hectares = house.money, house.record.endowment_hectares
        cls.games.step(cls.game, 2)
        cls.house = cls.game.view("cast")().actors[HOUSE]

    @classmethod
    def tearDownClass(cls):
        cls.games.close()

    def test_the_kind_is_an_answer_of_the_game_and_the_variants_house_is_of_it(self):
        kinds = {kind for answer in self.game.assembly.points["actor_kinds"]() for kind in answer}
        self.assertIn(KIND, kinds)
        self.assertEqual(self.house.record.kind, KIND)

    def test_the_houses_class_is_handed_the_narrowed_world_and_the_years_ran_on_it(self):
        self.assertEqual(type(self.house).narrowed_by_mod, MOD)
        self.assertGreater(self.house.record.endowment_hectares, self.start_hectares)

    def test_the_house_starts_with_no_money_and_the_endowment_the_entry_sets(self):
        self.assertEqual((self.start_money, self.start_hectares), (0.0, 40000.0))

    def test_the_house_collected_rent_and_bought_land_from_its_surplus(self):
        self.assertGreater(self.house.money, self.start_money)
        self.assertGreater(self.house.record.endowment_hectares, self.start_hectares)
        self.assertLessEqual(self.house.record.endowment_hectares, self.house.record.plan["land_ceiling_hectares"])


if __name__ == "__main__":
    unittest.main()
