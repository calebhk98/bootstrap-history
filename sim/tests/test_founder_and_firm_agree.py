"""The founder's business and a firm's are one object: the same plant owned by a seat and by a firm gives the same
crew, upkeep, takings and closing-decision inputs, and the founder's verbs move the plant, not a set of ids.

Stage 3a of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md."""
import unittest

from .harness import sim

from sim.agents import business_books
from sim.agents.api import ActorRecord, Business
from sim.engine.agents_port import SimWorld

OPENED_YEARS_AGO = 8


def founder_running_an_artisan_concern():
    """A game whose founder runs a plain concern (no capability institution, no scalable size) staffed by artisans."""
    game = sim(capital=1e9)
    world = SimWorld(game)
    for node_id, node in sorted(game.nodes.items()):
        if (node["up"] > 0.0 and node["rev"] > 0.0 and game.is_venture(node_id)
                and node_id not in game.CAPABILITY_INSTITUTIONS and node_id not in game.SCALABLE_INSTITUTIONS
                and set(world.concern_staff(node_id)) == {"artisan"}):
            break
    else:
        raise AssertionError("no plain artisan concern in the data")
    game.done.update(game.nodes[node_id]["pre"])
    game.done.add(node_id)
    game._done_changed()
    game.operating.add(node_id)
    game.state.projects.business.set_opened_year(node_id, game.year - OPENED_YEARS_AGO)
    return game, node_id


class FounderAndFirmAgree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game, cls.node_id = founder_running_an_artisan_concern()
        cls.world = SimWorld(cls.game)
        cls.seat_business = cls.game.state.projects.business
        cls.firm = cls.game.actors.add("firm:agree", ActorRecord(
            kind="firm", money=1e9, founded_year=cls.game.year - 20,
            business=Business.running([cls.node_id], opened_year=cls.game.year - OPENED_YEARS_AGO)))

    def test_both_own_the_same_plant(self):
        seat_plant, firm_plant = self.seat_business.plant_of(self.node_id), self.firm.business.plant_of(self.node_id)
        self.assertEqual((seat_plant.size, seat_plant.opened_year, seat_plant.state),
                         (firm_plant.size, firm_plant.opened_year, firm_plant.state))

    def test_same_crew(self):
        scholars, craftsmen = self.game.venture_hands(self.node_id)
        crew = self.world.concern_staff(self.node_id)
        self.assertEqual(scholars, 0.0)
        self.assertAlmostEqual(craftsmen, crew["artisan"] * self.seat_business.size_of(self.node_id), places=9)

    def test_same_upkeep(self):
        size = self.seat_business.size_of(self.node_id)
        self.assertAlmostEqual(self.game.venture_upkeep_quote(self.node_id)["now"], self.world.upkeep(self.node_id, size), places=6)

    def test_same_takings(self):
        opened = self.firm.business.opened_year_of(self.node_id, self.game.year)
        self.assertAlmostEqual(self.game.venture_real_earnings(self.node_id),
                               self.world.concern_takings(self.node_id, opened, 0.0, self.firm.business.size_of(self.node_id)), places=6)

    def test_same_closing_decision_inputs(self):
        # the ramp a closing decision weighs, and the margin once ramped (takings less upkeep)
        self.assertAlmostEqual(self.game.venture_ramp(self.node_id), business_books.ramp(self.firm.business, self.node_id, self.world), places=9)
        self.assertAlmostEqual(self.world.concern_margin(self.node_id),
                               self.world.concern_gross(self.node_id) - self.world.upkeep(self.node_id), places=9)


class FounderVerbsMoveThePlant(unittest.TestCase):
    def setUp(self):
        self.game, self.node_id = founder_running_an_artisan_concern()
        self.business = self.game.state.projects.business
        self.plant = self.business.plant_of(self.node_id)

    def test_closing_frees_its_crew_and_stops_its_outlays(self):
        crew_held, upkeep_before = self.game.venture_staff_used(), self.game.upkeep_by_concern().get(self.node_id, 0.0)
        self.assertGreater(upkeep_before, 0.0)
        ok, _message = self.game.close_venture(self.node_id)
        self.assertTrue(ok)
        self.assertEqual(self.business.state_of(self.node_id), "mothballed")
        self.assertNotIn(self.node_id, self.game.upkeep_by_concern())
        self.assertLess(self.game.venture_staff_used()[1], crew_held[1])
        self.assertEqual(self.game.state.projects.closures[self.node_id]["reason"], self.game.CLOSED_BY_CHOICE)

    def test_mothball_then_restore_returns_the_same_plant(self):
        self.business.set_size(self.node_id, 1.0)
        before = (self.plant.entry_key, self.plant.size, self.plant.opened_year)
        self.assertTrue(self.game.mothball_work(self.node_id)[0])
        self.assertIs(self.business.plant_of(self.node_id), self.plant)
        self.assertEqual(self.plant.state, "mothballed")
        ok, _message = self.game.restore_work(self.node_id)
        self.assertTrue(ok, _message)
        self.assertIs(self.business.plant_of(self.node_id), self.plant)
        self.assertEqual((self.plant.entry_key, self.plant.size, self.plant.opened_year), before)
        self.assertEqual(self.plant.state, "operating")
        self.assertEqual(self.plant.reason, "")
        self.assertIn(self.node_id, self.game.operating)

    def test_a_sold_plant_leaves_the_seat_with_its_size_and_age(self):
        party = self.game.seat_party(self.game.state.acting_seat)
        plant = party.release_plant(self.node_id, SimWorld(self.game))
        self.assertEqual((plant.size, plant.opened_year), (1.0, self.game.year - OPENED_YEARS_AGO))
        self.assertIsNone(self.business.plant_of(self.node_id))


if __name__ == "__main__":
    unittest.main()
