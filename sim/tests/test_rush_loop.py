"""The greedy loop of `rush` (`rush_loop.begin_in_order`) over nodes and callables built here, and `_rush_preview`'s promise
(the game is put back whatever the real run did) over a stand-in with the save and load replaced. No game is built. The caps
and filters themselves are test_rush_fiscal_controls and test_rush_filters."""
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.ui.proto import dispatch_ventures, rush_loop
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

NODES = {name: {"name": name.title(), "yrs": years, "ph": hours}
         for name, years, hours in (("a", 1, 10), ("b", 2, 10), ("c", 1, 10), ("d", 4, 10))}
COSTS = {"a": 100.0, "b": 200.0, "c": 300.0, "d": 400.0}


def walk(candidates="abcd", limit=None, hours_budget=1.0e9, cap_refusal=None, refuse=()):
    begun = []

    def begin(node_id, annual_draw):
        if node_id in refuse:
            return False, "refused " + node_id
        begun.append(node_id)
        return True, {"id": node_id, "annual_draw": annual_draw}

    result = rush_loop.begin_in_order(list(candidates), NODES, limit, hours_budget, 20.0, COSTS.get,
                                      cap_refusal or (lambda *args: None), begin)
    return result, begun


class BeginInOrder(unittest.TestCase):

    def test_everything_begins_in_the_order_given_when_nothing_stops_it(self):
        (started, not_started, hours, cost, draw), begun = walk()
        self.assertEqual(begun, list("abcd"))
        self.assertEqual([row["id"] for row in started], list("abcd"))
        self.assertEqual(not_started, [])
        self.assertEqual((hours, cost), (40.0, 1000.0))
        self.assertAlmostEqual(draw, 100.0 + 100.0 + 300.0 + 100.0)

    def test_the_annual_draw_is_the_cost_over_the_calendar_floor(self):
        (started, *_rest), _begun = walk()
        self.assertEqual({row["id"]: row["annual_draw"] for row in started}, {"a": 100.0, "b": 100.0, "c": 300.0, "d": 100.0})

    def test_a_limit_stops_after_that_many(self):
        (started, *_rest), begun = walk(limit=2)
        self.assertEqual(begun, ["a", "b"])
        self.assertEqual(len(started), 2)

    def test_a_cap_refusal_skips_that_one_and_goes_on_to_the_next(self):
        def refuse_c(cost, draw, cost_so_far, draw_so_far, hours, hours_so_far):
            return "past a cap" if cost == COSTS["c"] else None
        (started, not_started, *_rest), begun = walk(cap_refusal=refuse_c)
        self.assertEqual(begun, ["a", "b", "d"])
        self.assertEqual([(row["id"], row["why"]) for row in not_started], [("c", "past a cap")])

    def test_the_cap_sees_what_has_already_been_begun(self):
        seen = []
        walk(cap_refusal=lambda *args: seen.append(args[2:]) or None)
        self.assertEqual([entry[0] for entry in seen], [0.0, 100.0, 300.0, 600.0])      # cost so far
        self.assertEqual([entry[3] for entry in seen], [0.0, 10.0, 20.0, 30.0])         # hours so far

    def test_the_first_project_always_begins_however_small_the_hours_budget(self):
        (started, not_started, *_rest), begun = walk(hours_budget=5.0)
        self.assertEqual(begun, ["a"])
        self.assertEqual([row["id"] for row in not_started], list("bcd"))

    def test_hours_beyond_the_budget_are_not_begun_and_say_why(self):
        (started, not_started, hours, *_rest), begun = walk(hours_budget=25.0)
        self.assertEqual(begun, ["a", "b"])
        self.assertEqual(hours, 20.0)
        self.assertTrue(all(row["why"] for row in not_started))

    def test_a_start_that_is_refused_is_listed_with_its_reason_and_costs_nothing(self):
        (started, not_started, hours, cost, _draw), begun = walk(refuse=("b",))
        self.assertEqual(begun, ["a", "c", "d"])
        self.assertEqual(not_started, [{"id": "b", "why": "refused b"}])
        self.assertEqual((hours, cost), (30.0, 800.0))

    def test_every_candidate_is_either_started_or_listed(self):
        (started, not_started, *_rest), _begun = walk(hours_budget=25.0, refuse=("a",))
        self.assertEqual(sorted(row["id"] for row in started + not_started), list("abcd"))


class PreviewPutsTheGameBack(unittest.TestCase):

    def run_preview(self, rush):
        game = Game(order=["x", "y"])
        loaded = []
        with mock.patch.object(dispatch_ventures, "save_state"), \
                mock.patch.object(dispatch_ventures, "load_state", lambda sim, path: loaded.append(path)), \
                mock.patch.object(dispatch_ventures, "_cmd_rush", rush):
            try:
                reply = dispatch_ventures._rush_preview(game, {}, {"cmd": "rush"}, None)
            except RuntimeError:
                reply = None
        return game, loaded, reply

    def test_the_real_rush_is_run_forced_and_not_as_a_preview_and_its_start_list_becomes_the_preview(self):
        asked = []

        def rush(sim, nodes, cmd, ended):
            asked.append(cmd)
            sim.order.reverse()
            return {"ok": True, "count_started": 1, "started": [{"id": "x"}], "total_cost": 5.0, "total_annual_draw": 1.0,
                    "total_founder_hours": 2.0, "filters": {}, "trade_bottlenecks": [], "risk_exposure": [],
                    "count_not_started": 0, "not_started": []}
        game, loaded, reply = self.run_preview(rush)
        self.assertEqual((asked[0]["preview"], asked[0]["force"]), (False, True))
        self.assertEqual(reply["would_start"], [{"id": "x"}])
        self.assertIs(reply["nothing_changed"], True)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(game.order, ["x", "y"])

    def test_the_game_is_put_back_even_when_the_real_run_raises(self):
        def rush(sim, nodes, cmd, ended):
            sim.order.clear()
            raise RuntimeError("boom")
        game, loaded, reply = self.run_preview(rush)
        self.assertIsNone(reply)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(game.order, ["x", "y"])

    def test_a_refused_rush_is_handed_back_unchanged(self):
        game, loaded, reply = self.run_preview(lambda sim, nodes, cmd, ended: {"ok": False, "error": "no"})
        self.assertEqual(reply, {"ok": False, "error": "no"})
        self.assertEqual(len(loaded), 1)


if __name__ == "__main__":
    unittest.main()
