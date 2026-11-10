"""The year ledger's block writes (sim/economy/year_ledger_block_kernels.py through the views' `set_rows`, `set_many`, `replace_many`,
`add_many`) leave the tables as the per-item writes they stand for: the same figures, the same order of entry, the same rows."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy.year_ledger import YearLedger


def listed(view):
    """A figure view or a nested view as (key, figure) pairs in entry order, inner views as (sub, amount) pairs in row order."""
    return [(key, list(value.items()) if hasattr(value, "items") else value) for key, value in view.items()]


class FigureBlockTests(unittest.TestCase):
    def test_set_many_equals_setting_each_agent(self):
        names, amounts = ["c", "a", "b", "a"], [3.0, 1.5, 2.25, 4.0]
        block, plain = YearLedger(), YearLedger()
        block.spare_hours.set_many(names, numpy.array(amounts))
        for name, amount in zip(names, amounts):
            plain.spare_hours[name] = amount
        self.assertEqual(listed(block.spare_hours), [("c", 3.0), ("a", 4.0), ("b", 2.25)])
        self.assertEqual(listed(block.spare_hours), listed(plain.spare_hours))

    def test_set_many_keeps_the_place_of_a_member_and_changes_its_figure(self):
        block, plain = YearLedger(), YearLedger()
        for ledger in (block, plain):
            ledger.spare_hours.update({"x": 1.0, "y": 2.0})
        block.spare_hours.set_many(["y", "z", "x"], numpy.array([5.0, 6.0, 7.0]))
        for name, amount in (("y", 5.0), ("z", 6.0), ("x", 7.0)):
            plain.spare_hours[name] = amount
        self.assertEqual(listed(block.spare_hours), [("x", 7.0), ("y", 5.0), ("z", 6.0)])
        self.assertEqual(listed(block.spare_hours), listed(plain.spare_hours))

    def test_set_many_of_nothing_changes_nothing(self):
        ledger = YearLedger()
        ledger.spare_hours.set_many([], numpy.zeros(0))
        self.assertEqual(len(ledger.spare_hours), 0)

    def test_set_rows_of_markets_equals_setting_each_market(self):
        keys = [("grain", "rome"), ("wine", "ostia"), ("grain", "ostia")]
        amounts = [0.5, 2.0, 0.125]
        block, plain = YearLedger(), YearLedger()
        rows = numpy.array([block.tables.market_number(*key) for key in keys], dtype=numpy.int64)
        block.unmet_demand.set_rows(rows[[2, 0]], numpy.array([amounts[2], amounts[0]]))
        plain.unmet_demand[keys[2]], plain.unmet_demand[keys[0]] = amounts[2], amounts[0]
        self.assertEqual(listed(block.unmet_demand), [(keys[2], 0.125), (keys[0], 0.5)])
        self.assertEqual(listed(block.unmet_demand), listed(plain.unmet_demand))

    def test_seeded_random_agents_equal_the_loop(self):
        generator = random.Random(7)
        block, plain = YearLedger(), YearLedger()
        for _ in range(5):
            names = ["agent%d" % generator.randrange(40) for _ in range(30)]
            amounts = [generator.random() * 100 for _ in names]
            block.hours_sold.set_many(names, numpy.array(amounts))
            for name, amount in zip(names, amounts):
                plain.hours_sold[name] = amount
        self.assertEqual(listed(block.hours_sold), listed(plain.hours_sold))


class PairBlockTests(unittest.TestCase):
    def test_replace_many_equals_assigning_each_agent(self):
        block, plain = YearLedger(), YearLedger()
        for ledger in (block, plain):
            ledger.grown["old"] = {"rye": 2.0}
        names = ["new", "old", "last"]
        entries = [{"wheat": 1.0, "rye": 2.5}, {"barley": 4.0}, {}]
        block.grown.replace_many(names, entries)
        for name, mapping in zip(names, entries):
            plain.grown[name] = mapping
        self.assertEqual(listed(block.grown), [("old", [("barley", 4.0)]), ("new", [("wheat", 1.0), ("rye", 2.5)]), ("last", [])])
        self.assertEqual(listed(block.grown), listed(plain.grown))
        self.assertEqual(block.grown["new"]["rye"], 2.5)
        self.assertNotIn("rye", block.grown["old"])

    def test_add_many_equals_adding_into_each_agents_dict(self):
        block, plain = YearLedger(), YearLedger()
        for ledger in (block, plain):
            ledger.hours_hired["mill"] = {"smith": 10.0}
        employers = ["farm", "mill", "idle"]
        by_trade = [{"labourer": 3.5, "smith": 1.0}, {"smith": 0.25, "miller": 7.0}, {}]
        block.hours_hired.add_many(employers, by_trade)
        for employer, hired in zip(employers, by_trade):
            rows = plain.hours_hired.setdefault(employer, {})
            for trade, hours in hired.items():
                rows[trade] = rows.get(trade, 0.0) + hours
        self.assertEqual(listed(block.hours_hired), [("mill", [("smith", 10.25), ("miller", 7.0)]), ("farm", [("labourer", 3.5), ("smith", 1.0)]),
                                                     ("idle", [])])
        self.assertEqual(listed(block.hours_hired), listed(plain.hours_hired))

    def test_seeded_random_blocks_equal_the_loops(self):
        generator = random.Random(11)
        goods, trades = ["g%d" % number for number in range(9)], ["t%d" % number for number in range(5)]
        block, plain = YearLedger(), YearLedger()
        for _ in range(6):
            names = generator.sample(["a%d" % number for number in range(25)], 12)
            grown = [{good: generator.random() for good in generator.sample(goods, generator.randrange(4))} for _ in names]
            hired = [{trade: generator.random() * 9 for trade in generator.sample(trades, generator.randrange(4))} for _ in names]
            block.grown.replace_many(names, grown)
            block.hours_hired.add_many(names, hired)
            for name, mapping, hours in zip(names, grown, hired):
                plain.grown[name] = mapping
                rows = plain.hours_hired.setdefault(name, {})
                for trade, amount in hours.items():
                    rows[trade] = rows.get(trade, 0.0) + amount
        self.assertEqual(listed(block.grown), listed(plain.grown))
        self.assertEqual(listed(block.hours_hired), listed(plain.hours_hired))
        self.assertEqual(block.grown.as_plain(), plain.grown.as_plain())


if __name__ == "__main__":
    unittest.main()
