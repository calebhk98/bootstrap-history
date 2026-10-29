"""SMOKE: typed player commands reach the game on unopened games. An excluded node stays out of `rush preview`, `rush` and `auto_open`;
`rush preview` starts nothing and lists exactly the ids `rush limit` then starts; `quote` changes nothing; a school is founded by
every spelling. The exclusion list rules are test_exclusion_rules, the parser and screens test_player_command_fixes and
test_player_choice_routes. No years run."""
import unittest

from sim.knowledge.api import LearnTechnique
from sim.tests.harness import NODES, S, unopened_sim
from sim.ui.proto.typed import parse_typed
from sim.projects.api import AutoOpenVentures


def _typed(game, line):
    command, refusal = parse_typed(line)
    assert command is not None, (line, refusal)
    return S._agent_dispatch(game, NODES, command)


def _ids(rows):
    return [row["id"] for row in rows]


class RushPreviewAndExclusionsTest(unittest.TestCase):
    def test_preview_starts_nothing_and_lists_the_ids_rush_then_starts_leaving_out_an_excluded_node(self):
        game = unopened_sim(capital=2_000_000)
        victim = next(node_id for node_id in game.view("project_order")() if game.view("start_check")(node_id, False, None, False)[0])
        self.assertTrue(_typed(game, "exclude %s" % victim)["ok"])
        self.assertIn(victim, game.view("exclusions")())
        preview = _typed(game, "rush preview limit:3")
        self.assertFalse(game.active)
        self.assertNotIn(victim, _ids(preview["would_start"]))
        self.assertIn(victim, _ids(preview["excluded"]))
        self.assertTrue(all(row.get("why") for row in preview["excluded"]))
        real = _typed(game, "rush limit:3")
        self.assertEqual(len(real["started"]), 3)
        self.assertEqual(_ids(preview["would_start"]), _ids(real["started"]))
        self.assertNotIn(victim, game.active)

    def test_auto_open_skips_an_excluded_concern(self):
        game = unopened_sim(capital=2_000_000)
        venture = next(node_id for node_id in NODES if game.view("is_venture")[node_id] and NODES[node_id]["rev"] > NODES[node_id]["up"])
        game.send(LearnTechnique(venture))
        game.view("exclusions")().add(venture)
        game.send(AutoOpenVentures())
        self.assertNotIn(venture, game.state.projects.operating)


class QuoteAndSchoolTest(unittest.TestCase):
    def test_quote_answers_for_every_target_and_changes_nothing_and_a_school_is_founded_by_every_spelling(self):
        game = unopened_sim(capital=1_000_000)
        self.assertTrue(_typed(game, "quote manumit 1").get("ok"))
        capital = game.state.household.capital
        _typed(game, "quote farm 20")
        self.assertEqual(game.state.household.capital, capital)
        game.state.seats[game.state.acting_seat].modules["workforce"].trades_created.add("chemist")
        game.view("legacy_labour")().market.press("chemist", 100)
        for line in ("buy school chemist 1", "buy trade school chemist 1", "buy trade_school chemist 1"):
            reply = _typed(game, line)
            self.assertTrue(reply.get("ok"), (line, reply))
            self.assertEqual(reply["trade"], "chemist", line)


if __name__ == "__main__":
    unittest.main()
