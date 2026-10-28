"""SMOKE: `available` on an unopened Rome game reads the game's staff and money, finds nothing cleanly and treats a quoted subject like an
unquoted one; absurd quantities are refused by the one reader. The marker rule is test_short_of_staff_marker, the paging
test_heard_paging. No years run."""
import unittest

from sim.tests.harness import NODES, S, unopened_sim


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


class AvailableReplyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim()

    def test_each_row_says_what_staff_it_needs_and_is_marked_short_exactly_when_the_start_gate_would_refuse(self):
        reply = _ask(self.game, cmd="available", find="flax")
        rows = reply.get("available") or []
        self.assertIsNotNone(reply.get("you_could_raise_for_a_project"))
        self.assertTrue(any(row.get("needs_staff") for row in rows))
        labour = self.game.view("legacy_labour")()
        for row in rows:
            node = NODES[row["id"]]
            short = node["art"] > labour.craft_hands_available() + 1e-9 or node["sch"] > labour.effective_scholars() + 1e-9
            self.assertEqual(bool(row.get("short_of_staff")), short, row["id"])

    def test_a_search_that_matches_nothing_says_so(self):
        self.assertTrue(_ask(self.game, cmd="available", find="zzzznosuchthing").get("nothing_matched"))

    def test_a_quoted_subject_means_the_same_as_an_unquoted_one(self):
        quoted = _ask(self.game, cmd="available", subject='"power and precision"')
        plain = _ask(self.game, cmd="available", subject="power and precision")
        self.assertEqual(quoted.get("count"), plain.get("count"))
        self.assertGreater(quoted.get("count", 0), 0)

    def test_an_absurd_quantity_is_refused_and_an_ordinary_one_goes_through_the_same_reader(self):
        self.assertIs(_ask(self.game, cmd="hire", trade="smith", n=1e21).get("ok"), False)
        self.assertIs(_ask(self.game, cmd="buy", what="forest", n=1e30).get("ok"), False)
        self.assertIsNotNone(_ask(self.game, cmd="buy", what="forest", n=3).get("ok"))

if __name__ == "__main__":
    unittest.main()
