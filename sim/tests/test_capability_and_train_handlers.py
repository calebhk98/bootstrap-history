"""The `ventures`, `mothball` and `train` commands over a stand-in game (no game is built): a capability institution is told apart
from an ordinary concern, and the first training of a new trade says hiring is a second step. Each handler is called as
the dispatcher calls it. The membership rule (`CAPABILITY_INSTITUTIONS`) is data from the `capability` mechanic, tested in
test_round8g_display."""
import unittest
from types import SimpleNamespace

from sim.refusal import LogLine

from sim.ui.proto.dispatch_labour import _cmd_train
from sim.ui.proto.dispatch_ventures import _cmd_mothball, _cmd_ventures
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

CAPABILITY = "identity_cover"
ORDINARY = "tex_horizontal_loom"
NODES = {CAPABILITY: {"name": "Identity cover"}, ORDINARY: {"name": "Horizontal loom"}}


def _ventures_stand_in(idle):
    labour = Game(craft_trades_report=lambda: {"craft": ["smith"], "not_craft": ["labourer"]},
                             effective_scholars=lambda: 1.0)
    return Game(
        CAPABILITY_INSTITUTIONS=frozenset({CAPABILITY}), FOUNDER_IS_WORTH=1.0, founder_alive=True, view=lambda name: (lambda: {"artisans": 2.0}),
        done=set(idle), operating=set(), labour=labour, policy={}, year=100, capital=1000.0,
        state=Game(projects=Game(keep_staffed=set()), acting_record=Game(seat_progress=Game(_said_explanations=None))),
        is_venture=lambda node_id: True, venture_capex=lambda node_id: 100.0, venture_staff_free=lambda: (1.0, 1.0),
        venture_staff_used=lambda: (0.0, 0.0), venture_staff_who_is_watching_what=lambda: [],
        venture_forecast_basis=lambda node_id: "forecast", venture_sale_basis=lambda node_id: "sale",
        venture_foreman=lambda node_id: (None, 0.0), venture_hands=lambda node_id: (0.1, 0.2),
        venture_real_earnings=lambda node_id: 10.0,
        venture_upkeep_quote=lambda node_id: {"now": 5.0, "at_full_staffing": 6.0})


class VenturesSeparatesCapabilities(unittest.TestCase):

    def test_an_idle_capability_is_in_its_own_list_and_an_ordinary_concern_in_the_ordinary_one(self):
        reply = _cmd_ventures(_ventures_stand_in([CAPABILITY, ORDINARY]), NODES, {}, None)
        capability_ids = [row["id"] for row in reply["capabilities_you_know_how_to_run_but_have_not_opened"]]
        ordinary_ids = [row["id"] for row in reply["you_know_how_but_have_not_opened"]]
        self.assertEqual(capability_ids, [CAPABILITY])
        self.assertEqual(ordinary_ids, [ORDINARY])

    def test_only_the_capability_row_carries_the_capability_marker(self):
        reply = _cmd_ventures(_ventures_stand_in([CAPABILITY, ORDINARY]), NODES, {}, None)
        self.assertIn("capability", reply["capabilities_you_know_how_to_run_but_have_not_opened"][0])
        self.assertNotIn("capability", reply["you_know_how_but_have_not_opened"][0])


def _mothball_stand_in():
    game = Game(CAPABILITY_INSTITUTIONS=frozenset({CAPABILITY}), year=100, log=[],
                           mothball_work=lambda node_id: (True, "shut " + node_id), upkeep=lambda: 3.0)
    game.send = lambda command: ((True, "shut " + command.node_id) if type(command).__name__ == "MothballWork"
                                 else game.log.append((game.year, LogLine(command.kind, command.text, **command.facts))))
    return game


class MothballWarnsOfALostCapability(unittest.TestCase):

    def test_mothballing_a_capability_carries_the_but(self):
        reply = _cmd_mothball(_mothball_stand_in(), NODES, {"id": CAPABILITY}, None)
        self.assertTrue(reply["ok"])
        self.assertTrue(reply.get("but"))

    def test_mothballing_an_ordinary_concern_carries_no_but(self):
        reply = _cmd_mothball(_mothball_stand_in(), NODES, {"id": ORDINARY}, None)
        self.assertTrue(reply["ok"])
        self.assertNotIn("but", reply)


def _train_stand_in():
    labour = Game(
        train_check=lambda trade, quantity, source: ({"count": quantity}, None),
        trainee_wage_bill=lambda trade, count: 10.0 * count,
        train=lambda trade, quantity, source: (True, "teaching %d %s" % (quantity, trade)),
        director_pool=lambda: 100.0, director_hours_committed=lambda: 10.0)
    return Game(labour=labour, capital=500.0)


class TrainSaysHiringIsASecondStep(unittest.TestCase):

    def test_training_a_trade_this_society_lacks_says_how_to_hire_into_it(self):
        reply = _cmd_train(_train_stand_in(), NODES, {"trade": "machinist", "n": 1}, None)
        self.assertTrue(reply["ok"])
        self.assertTrue(reply.get("means"))

    def test_training_a_trade_the_society_has_adds_no_such_note(self):
        reply = _cmd_train(_train_stand_in(), NODES, {"trade": "smith", "n": 1}, None)
        self.assertTrue(reply["ok"])
        self.assertNotIn("means", reply)


if __name__ == "__main__":
    unittest.main()
