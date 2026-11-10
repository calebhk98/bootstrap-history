"""The workforce views that are cached: each is read, a writer of what it reads writes, and the next read is the fresh value."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.assembly.api import Operations
from sim.labour import trade_data
from sim.labour.market import trades as market_trades
from sim.tests import workforce_assembly
from sim.workforce.commands import NoteClearedWage

REGISTRY_RECORDS = {"digger": SimpleNamespace(family="earth", training_years=0.0, extra={"fallback": True}),
                    "smith": SimpleNamespace(family="metal", training_years=4.0, extra={})}


def build(records=None, **answers):
    return workforce_assembly.build({"trade_records": REGISTRY_RECORDS if records is None else records, **answers})


class TradeRegistryView(unittest.TestCase):
    def test_the_registry_is_each_trades_family_years_and_extra_fields(self):
        assembly, _workforce = build()
        self.assertEqual(assembly.views["trade_registry"](), {"digger": {"family": "earth", "training_years": 0.0, "fallback": True},
                                                              "smith": {"family": "metal", "training_years": 4.0}})

    def test_the_registry_is_the_same_object_while_the_records_stand(self):
        assembly, _workforce = build()
        self.assertIs(assembly.views["trade_registry"](), assembly.views["trade_registry"]())

    def test_new_records_after_a_load_give_a_new_registry(self):
        records = dict(REGISTRY_RECORDS)
        answers = {"trade_records": lambda: records}
        assembly, _workforce = workforce_assembly.build(answers)
        self.assertEqual(sorted(assembly.views["trade_registry"]()), ["digger", "smith"])
        records = {"porter": SimpleNamespace(family="carry", training_years=0.0, extra={})}
        answers["trade_records"] = lambda: records
        assembly.clock.bump_everything()
        self.assertEqual(sorted(assembly.views["trade_registry"]()), ["porter"])


class UnskilledTradeView(unittest.TestCase):
    def test_the_flagged_trade_is_found_once_while_the_registry_stands(self):
        assembly, _workforce = build()
        with mock.patch.object(market_trades, "fallback_trade_of_registry", wraps=market_trades.fallback_trade_of_registry) as scan:
            self.assertEqual(assembly.views["unskilled_trade"](), "digger")
            self.assertEqual(assembly.views["unskilled_trade"](), "digger")
        self.assertEqual(scan.call_count, 1)

    def test_the_trade_follows_new_records(self):
        records = {"digger": REGISTRY_RECORDS["digger"]}
        assembly, _workforce = workforce_assembly.build({"trade_records": lambda: records})
        self.assertEqual(assembly.views["unskilled_trade"](), "digger")
        records = {"porter": SimpleNamespace(family="carry", training_years=0.0, extra={"fallback": True})}
        assembly.clock.bump_everything()
        self.assertEqual(assembly.views["unskilled_trade"](), "porter")

    def test_a_mod_adjuster_of_the_view_still_applies(self):
        adjust = Operations("renamer", adjusters={"unskilled_trade": ((lambda access, value: value + "_adjusted", ()),)})
        assembly, _workforce = workforce_assembly.build({"trade_records": REGISTRY_RECORDS}, operations=[adjust])
        self.assertEqual(assembly.views["unskilled_trade"](), "digger_adjusted")
        self.assertEqual(assembly.views["unskilled_trade"](), "digger_adjusted")


class FallbackTradeOfRegistry(unittest.TestCase):
    def test_one_registry_object_is_scanned_once_however_often_it_is_asked(self):
        registry = {"digger": {"fallback": True}, "smith": {}}
        world = SimpleNamespace(trades=SimpleNamespace(trade_registry=registry))
        with mock.patch.object(market_trades, "fallback_trade_of_registry", wraps=market_trades.fallback_trade_of_registry) as scan:
            answers = [trade_data.fallback_trade_of(world) for _ in range(5)]
        self.assertEqual(answers, ["digger"] * 5)
        self.assertEqual(scan.call_count, 1)

    def test_the_unskilled_role_shares_the_scan(self):
        registry = {"digger": {"fallback": True}, "smith": {"role": "smith"}}
        world = SimpleNamespace(trades=SimpleNamespace(trade_registry=registry))
        with mock.patch.object(market_trades, "fallback_trade_of_registry", wraps=market_trades.fallback_trade_of_registry) as scan:
            answers = [trade_data.trade_of_role(registry, "unskilled"), trade_data.fallback_trade_of(world)]
        self.assertEqual(answers, ["digger", "digger"])
        self.assertEqual(scan.call_count, 1)

    def test_another_registry_object_is_scanned_afresh(self):
        first = SimpleNamespace(trades=SimpleNamespace(trade_registry={"digger": {"fallback": True}}))
        second = SimpleNamespace(trades=SimpleNamespace(trade_registry={"porter": {"fallback": True}}))
        self.assertEqual([trade_data.fallback_trade_of(first), trade_data.fallback_trade_of(second), trade_data.fallback_trade_of(first)],
                         ["digger", "porter", "digger"])


class IsCraftTradeView(unittest.TestCase):
    def test_a_trade_is_craft_when_its_family_is(self):
        families = {"smith": "craft", "digger": "earth"}
        assembly, _workforce = build(trade_family=lambda trade: families[trade])
        self.assertTrue(assembly.views["is_craft_trade"]["smith"])
        self.assertFalse(assembly.views["is_craft_trade"]["digger"])

    def test_the_answer_is_kept_until_the_content_is_read_again(self):
        families = {"smith": "craft"}
        calls = []
        assembly, _workforce = build(trade_family=lambda trade: calls.append(trade) or families[trade])
        assembly.views["is_craft_trade"]["smith"]
        assembly.views["is_craft_trade"]["smith"]
        self.assertEqual(calls, ["smith"])
        families["smith"] = "metal"
        assembly.clock.bump_everything()
        self.assertFalse(assembly.views["is_craft_trade"]["smith"])


class ClearedWageChangeView(unittest.TestCase):
    def test_there_is_no_change_before_two_clearings(self):
        assembly, _workforce = build()
        self.assertIsNone(assembly.views["cleared_wage_change"]())
        assembly.handlers[NoteClearedWage](NoteClearedWage(2.0))
        self.assertIsNone(assembly.views["cleared_wage_change"]())

    def test_each_clearing_the_view_reads_the_move_since_the_one_before(self):
        assembly, _workforce = build()
        assembly.handlers[NoteClearedWage](NoteClearedWage(2.0))
        assembly.views["cleared_wage_change"]()
        assembly.handlers[NoteClearedWage](NoteClearedWage(3.0))
        self.assertAlmostEqual(assembly.views["cleared_wage_change"](), 0.5)
        assembly.handlers[NoteClearedWage](NoteClearedWage(1.5))
        self.assertAlmostEqual(assembly.views["cleared_wage_change"](), -0.5)

    def test_a_clearing_that_set_no_wage_leaves_no_change(self):
        assembly, _workforce = build()
        assembly.handlers[NoteClearedWage](NoteClearedWage(2.0))
        assembly.handlers[NoteClearedWage](NoteClearedWage(3.0))
        assembly.views["cleared_wage_change"]()
        assembly.handlers[NoteClearedWage](NoteClearedWage(None))
        self.assertIsNone(assembly.views["cleared_wage_change"]())


class ConstantViews(unittest.TestCase):
    def test_the_labour_market_is_the_one_object_every_read(self):
        assembly, workforce = build()
        self.assertIs(assembly.views["labour_market"](), workforce.parts.core.labour.market)
        self.assertIs(assembly.views["labour_market"](), assembly.views["labour_market"]())

    def test_the_state_weights_and_literacy_references_are_kept(self):
        assembly, _workforce = build()
        for name in ("labour_state_weights", "literacy_references"):
            self.assertIs(assembly.views[name](), assembly.views[name]())


class CachedViewsAreDeclared(unittest.TestCase):
    def test_these_workforce_views_are_cached(self):
        assembly, _workforce = build()
        for name in ("trade_registry", "unskilled_trade", "is_craft_trade", "cleared_wage_change", "labour_market",
                     "labour_state_weights", "literacy_references"):
            self.assertTrue(assembly.views[name].spec.cached, name)


if __name__ == "__main__":
    unittest.main()
