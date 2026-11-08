"""The year ledger's dict-like views (sim/economy/year_ledger_views.py, year_ledger_pair_views.py) behave as the dicts they replaced:
lookup, assignment, removal, order of entry, equality with a dict, live inner dicts, and no numbering from a read."""

QUICK_TOPIC = True

import pickle
import unittest

from sim.economy import year_ledger_tables
from sim.economy.year_ledger import YearLedger


class AgentFigureViewTests(unittest.TestCase):
    def test_assigning_adding_and_reading_back(self):
        ledger = YearLedger()
        ledger.money_out["b"] = 2.0
        ledger.money_out["a"] = 1.0
        ledger.money_out.add("b", 0.5)
        self.assertEqual(list(ledger.money_out.items()), [("b", 2.5), ("a", 1.0)])
        self.assertEqual((ledger.money_out["a"], ledger.money_out.get("zz", -1.0), "a" in ledger.money_out, "zz" in ledger.money_out, len(ledger.money_out)),
                         (1.0, -1.0, True, False, 2))
        self.assertEqual(ledger.money_out, {"a": 1.0, "b": 2.5})
        with self.assertRaises(KeyError):
            ledger.money_out["zz"]

    def test_removing_an_agent_and_entering_again_puts_it_last(self):
        ledger = YearLedger()
        ledger.sales_in.update({"a": 1.0, "b": 2.0})
        del ledger.sales_in["a"]
        ledger.sales_in["a"] = 5.0
        self.assertEqual(list(ledger.sales_in), ["b", "a"])
        self.assertEqual(ledger.sales_in.pop("b"), 2.0)
        self.assertEqual(ledger.sales_in, {"a": 5.0})

    def test_reading_a_name_never_numbers_it(self):
        ledger = YearLedger()
        before = len(ledger.tables.book.agent_ids)
        ledger.money_out.get("stranger", 0.0)
        ledger.hours_hired.get("stranger", {})
        ledger.sold.get(("stranger", "grain"))
        ledger.running_costs("stranger")
        self.assertEqual(len(ledger.tables.book.agent_ids), before)
        self.assertEqual(len(ledger.tables.book.good_ids), 0)

    def test_many_agents_grow_the_tables_and_keep_the_order(self):
        ledger = YearLedger()
        names = ["agent%03d" % number for number in range(300, 0, -1)]
        for number, name in enumerate(names):
            ledger.wages_in[name] = float(number)
        self.assertEqual(list(ledger.wages_in), names)
        self.assertEqual(ledger.wages_in["agent001"], 299.0)

    def test_running_costs_leave_out_plant(self):
        ledger = YearLedger()
        ledger.money_out["mill"] = 50.0
        ledger.plant_spend["mill"] = 30.0
        self.assertEqual((ledger.running_costs("mill"), ledger.running_costs("nobody")), (20.0, 0.0))


    def test_reading_many_agents_at_once_gives_the_default_for_non_members(self):
        ledger = YearLedger()
        ledger.sales_in["a"] = 4.0
        ledger.money_out["a"] = 10.0
        ledger.plant_spend["a"] = 3.0
        ledger.money_out["b"] = 1.0
        ledger.plant_spend["b"] = 5.0
        self.assertEqual(ledger.sales_in.values_of(["b", "a", "never"]).tolist(), [0.0, 4.0, 0.0])
        self.assertEqual(ledger.running_costs_of(["a", "b", "never"]).tolist(), [7.0, 0.0, 0.0])


class MarketFigureViewTests(unittest.TestCase):
    def test_keys_are_good_and_area(self):
        ledger = YearLedger()
        ledger.unmet_demand[("wheat", "rome")] = 4.0
        ledger.unmet_demand[("wine", "rome")] = 1.0
        self.assertEqual(list(ledger.unmet_demand.items()), [(("wheat", "rome"), 4.0), (("wine", "rome"), 1.0)])
        self.assertEqual(ledger.unmet_demand.get(("wheat", "gaul"), 0.0), 0.0)


class PairViewTests(unittest.TestCase):
    def test_rows_keep_the_order_they_were_made_and_a_removed_key_comes_back_last(self):
        ledger = YearLedger()
        ledger.sold[("a", "wheat")] = 1.0
        ledger.sold[("b", "wheat")] = 2.0
        ledger.sold[("a", "wine")] = 3.0
        del ledger.sold[("b", "wheat")]
        ledger.sold[("b", "wheat")] = 4.0
        self.assertEqual(list(ledger.sold.items()), [(("a", "wheat"), 1.0), (("a", "wine"), 3.0), (("b", "wheat"), 4.0)])
        self.assertEqual((("b", "wheat") in ledger.sold, ("b", "oil") in ledger.sold, len(ledger.sold)), (True, False, 3))

    def test_hours_hired_by_market_holds_hours_and_money(self):
        ledger = YearLedger()
        ledger.hours_hired_by_market[("farm", "plough", "north")] = (10.0, 25.0)
        self.assertEqual(list(ledger.hours_hired_by_market.items()), [(("farm", "plough", "north"), (10.0, 25.0))])
        self.assertEqual(ledger.hours_hired_by_market.get(("farm", "plough", "south")), None)

    def test_foreign_money_is_keyed_by_the_good_of_a_sale_or_the_purpose(self):
        ledger = YearLedger()
        ledger.imports_paid[("trader", "wine")] = 3.0
        ledger.imports_paid[("trader", "customs dues")] = 1.0
        self.assertEqual(ledger.imports_paid, {("trader", "wine"): 3.0, ("trader", "customs dues"): 1.0})
        self.assertEqual(ledger.imports_paid[("trader", "wine")], 3.0)


class NestedViewTests(unittest.TestCase):
    def test_setdefault_gives_the_live_inner_dict(self):
        ledger = YearLedger()
        rows = ledger.hours_hired.setdefault("farm", {})
        rows["plough"] = rows.get("plough", 0.0) + 40.0
        rows["mill"] = 2.0
        self.assertEqual(ledger.hours_hired, {"farm": {"plough": 40.0, "mill": 2.0}})
        self.assertEqual(list(ledger.hours_hired["farm"]), ["plough", "mill"])

    def test_assigning_a_dict_replaces_the_agents_rows_and_keeps_its_place(self):
        ledger = YearLedger()
        ledger.grown["a"] = {"wheat": 1.0, "oil": 2.0}
        ledger.grown["b"] = {"wheat": 5.0}
        ledger.grown["a"] = {"wine": 7.0}
        self.assertEqual(list(ledger.grown.items()), [("a", {"wine": 7.0}), ("b", {"wheat": 5.0})])
        self.assertEqual(ledger.grown.get("a", {}).get("oil", 0.0), 0.0)

    def test_an_agent_with_an_empty_dict_is_present(self):
        ledger = YearLedger()
        ledger.received["a"] = {}
        self.assertEqual((list(ledger.received), len(ledger.received), dict(ledger.received["a"])), (["a"], 1, {}))
        self.assertEqual(ledger.received.get("b", {}), {})

    def test_removing_an_inner_key_and_an_agent(self):
        ledger = YearLedger()
        ledger.hours_hired["a"] = {"plough": 1.0, "mill": 2.0, "saw": 3.0}
        del ledger.hours_hired["a"]["mill"]
        self.assertEqual(ledger.hours_hired, {"a": {"plough": 1.0, "saw": 3.0}})
        del ledger.hours_hired["a"]
        self.assertEqual((ledger.hours_hired, "a" in ledger.hours_hired), ({}, False))

    def test_many_rows_grow_the_table(self):
        ledger = YearLedger()
        for number in range(400):
            ledger.received.setdefault("a%d" % (number % 7), {})["good%d" % number] = float(number)
        self.assertEqual(sum(len(rows) for rows in ledger.received.values()), 400)
        self.assertEqual(ledger.received["a3"]["good10"], 10.0)


class TableTypesTests(unittest.TestCase):
    def test_every_table_type_pickles_by_module_and_name_so_kernels_load_from_the_cache(self):
        for name in ("AgentFigures", "PairRows", "MarketFigures", "ClearingRounds", "PairTarget"):
            kind = getattr(year_ledger_tables, name)
            self.assertIs(pickle.loads(pickle.dumps(kind)), kind)


if __name__ == "__main__":
    unittest.main()
