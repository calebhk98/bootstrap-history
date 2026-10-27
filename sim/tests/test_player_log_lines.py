"""What the player's own commands write to the log: `hire` and `fire` append a kinded line, and the log reply
reports each line's kind and facts. Handlers and the reply are called on a hand-built stand-in for the game."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.refusal import LogLine
from sim.ui.proto.dispatch_labour import _cmd_fire, _cmd_hire
from sim.ui.proto.state_log import _agent_log
from sim.tests.ui_stand_in import Game


class StandInLabour:
    """The labour market's answers a hire or a let-go reads."""

    def __init__(self, staff):
        self.staff = staff

    def wage_bill(self):
        return 0.0

    def hire_check(self, trade, quantity):
        return quantity, 10.0, None

    def hire(self, trade, quantity):
        self.staff.employees[trade] = self.staff.employees.get(trade, 0.0) + quantity
        return True, "%d %ss taken on" % (quantity, trade)

    def fire(self, trade, quantity):
        self.staff.employees[trade] = self.staff.employees.get(trade, 0.0) - quantity
        return True, "%d %s let go" % (quantity, trade)


def stand_in_game():
    game = Game(log=[], year=100, employees={}, capital=0.0, wages_prepaid=0.0, fog=False,
                           founder_alive=True, forgotten={}, nodes={}, state=Game(interface={}))
    game.labour = StandInLabour(game)
    game.view = lambda name: (lambda: {"employees": game.employees, "prepaid": game.wages_prepaid})
    game.send = lambda command: game.log.append((game.year, LogLine(command.kind, command.text, **command.facts)))
    game.living_cost = lambda: 0.0
    game.fog_scrub = lambda text: text
    game.deputies_carry_the_work = lambda: False
    return game


class PlayerLogTests(unittest.TestCase):
    def test_hiring_appends_a_hire_ordered_line(self):
        game = stand_in_game()
        reply = _cmd_hire(game, {}, {"cmd": "hire", "trade": "smith", "n": 2}, None)
        self.assertTrue(reply["ok"])
        self.assertEqual([(year, line.kind) for year, line in game.log], [(100, "hire_ordered")])

    def test_letting_go_appends_a_let_go_ordered_line(self):
        game = stand_in_game()
        game.employees["smith"] = 2.0
        reply = _cmd_fire(game, {}, {"cmd": "fire", "trade": "smith", "n": 1}, None)
        self.assertTrue(reply["ok"])
        self.assertEqual([(year, line.kind) for year, line in game.log], [(100, "let_go_ordered")])

    def test_a_refused_hire_writes_nothing(self):
        game = stand_in_game()
        game.labour.hire = lambda trade, quantity: (False, "no one to be had")
        reply = _cmd_hire(game, {}, {"cmd": "hire", "trade": "smith", "n": 2}, None)
        self.assertFalse(reply["ok"])
        self.assertEqual(game.log, [])

    def test_the_log_reply_carries_each_lines_kind_and_facts(self):
        game = stand_in_game()
        game.log = [(100, LogLine("project_started", "started: Foo", node="foo")),
                    (101, LogLine("hire_ordered", "taken on")),
                    (102, "a plain line")]
        entries = _agent_log(game, {"order": "oldest"})["entries"]
        self.assertEqual([entry.get("event_kind") for entry in entries], ["project_started", "hire_ordered", None])
        self.assertEqual(entries[0]["facts"], {"node": "foo"})

    def test_the_log_defaults_to_most_recent_first(self):
        game = stand_in_game()
        game.log = [(100, "a"), (105, "b"), (103, "c")]
        years = [entry["year"] for entry in _agent_log(game, {})["entries"]]
        self.assertEqual(years, sorted(years, reverse=True))


if __name__ == "__main__":
    unittest.main()
