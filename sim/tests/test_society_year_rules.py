"""The society's slow clock on stand-in games: literacy moves only where a school runs, a taught trade becomes the
society's own and grows toward its ceiling, and how much of a running concern's edge has leaked to competitors."""

QUICK_TOPIC = True

import unittest

from sim.diffusion import constants
from sim.diffusion.module import Diffusion
from sim.diffusion.state import DiffusionWorld
from sim.reporting.api import RecordEvent
from sim.tests import literacy_stand_in, module_harness
from sim.workforce.api import NoteTradeSpread, SetEmployed

TRADE = "electrician"


class Literacy:
    """A country's literacy that records how schools were told to move it."""

    def __init__(self):
        self.values = {"literacy_general": 0.1, "literacy_elite": 0.5}
        self.schooled = []

    def copy(self):
        return self

    def get(self, field):
        return self.values[field]

    def school(self, field, fraction, ceiling):
        self.schooled.append((field, fraction, ceiling))
        self.values[field] += fraction * (ceiling - self.values[field])


def schooling(flow):
    """A module whose schools teach at `flow`, and the literacy it moves."""
    literacy = Literacy()

    class Schooling(Diffusion):
        def effective_schooling_flow(self, field=None):
            return flow

        def literacy_ceiling(self, field):
            return {"literacy_elite": 0.97, "common": 0.9}[field]
    views, answers = literacy_stand_in.over(literacy)
    return module_harness.build(Schooling, views=views, answers=answers, world=DiffusionWorld()), literacy


class SchoolLiteracy(unittest.TestCase):

    def test_with_no_school_running_nothing_moves_and_nobody_is_taught(self):
        module, literacy = schooling(0.0)
        self.assertEqual(module._school_literacy(), {})
        self.assertEqual(literacy.schooled, [])

    def test_a_school_moves_each_figure_toward_its_own_ceiling_at_its_rate_times_the_flow(self):
        module, literacy = schooling(2.0)
        changed = module._school_literacy()
        self.assertEqual(literacy.schooled, [
            ("literacy_elite", constants.LITERACY_GROWTH_RATE_ELITE * 2.0, 0.97),
            ("literacy_general", constants.LITERACY_GROWTH_RATE_GENERAL * 2.0, 0.9)])
        self.assertEqual(sorted(changed), ["literacy_elite", "literacy_general"])
        self.assertLess(literacy.values["literacy_general"], 0.9)


def absorbing(created=(), introduced=None, endemic=(), employees=None, flow=3.0, years_needed=50.0, ceiling=10.0):
    """A module over a household that taught `created` trades, with `flow` of schooling and `years_needed` to absorb."""
    spread = {"absent": [TRADE], "created": set(created), "endemic": set(endemic),
              "introduced_year": dict(introduced or {})}

    class Absorbing(Diffusion):
        def schooling_flow(self, field=None):
            return flow

        def trade_absorption_years(self, flow):
            return years_needed
    return module_harness.build(Absorbing, views={
        "trade_spread": lambda: spread, "staff": lambda: {"employees": dict(employees or {})},
        "literacy_capacity": lambda trade: ceiling}, world=DiffusionWorld())


class TradeAbsorption(unittest.TestCase):

    def test_the_first_year_a_taught_trade_is_seen_only_records_its_introduction(self):
        module = absorbing(created={TRADE})
        module.advance_trade_absorption(100)
        self.assertEqual(module_harness.sent(module), [NoteTradeSpread(TRADE, introduced_year=100)])

    def test_a_trade_never_taught_here_is_left_alone(self):
        module = absorbing()
        module.advance_trade_absorption(100)
        self.assertEqual(module_harness.sent(module), [])

    def test_once_its_years_are_up_with_a_school_running_the_trade_becomes_the_societys_own(self):
        module = absorbing(created={TRADE}, introduced={TRADE: 100}, years_needed=50.0)
        module.advance_trade_absorption(150)
        first, event = module_harness.sent(module)
        self.assertEqual(first, NoteTradeSpread(TRADE, endemic=True))
        self.assertEqual((type(event), event.kind), (RecordEvent, "trade_no_longer_only_yours"))

    def test_before_its_years_are_up_it_is_not(self):
        module = absorbing(created={TRADE}, introduced={TRADE: 100}, years_needed=50.0)
        module.advance_trade_absorption(149)
        self.assertEqual(module_harness.sent(module), [])

    def test_with_no_school_running_it_never_becomes_endemic_however_long_it_has_been(self):
        module = absorbing(created={TRADE}, introduced={TRADE: 0}, flow=0.0)
        module.advance_trade_absorption(1000)
        self.assertEqual(module_harness.sent(module), [])

    def test_an_endemic_trade_grows_toward_the_same_ceiling_a_founder_hiring_is_held_to(self):
        module = absorbing(created={TRADE}, introduced={TRADE: 0}, endemic={TRADE}, employees={TRADE: 2.0}, ceiling=12.0)
        module.advance_trade_absorption(10)
        (command,) = module_harness.sent(module)
        self.assertEqual((type(command), command.trade), (SetEmployed, TRADE))
        self.assertTrue(2.0 < command.headcount < 12.0)

    def test_an_endemic_trade_at_its_ceiling_is_not_changed(self):
        module = absorbing(employees={TRADE: 12.0}, ceiling=12.0)
        module.grow_endemic_trade(TRADE)
        self.assertEqual(module_harness.sent(module), [])


def venturing(operating, nodes, opened_year=80, year=100, half_life=20.0):
    """A module over ventures `operating`, opened in `opened_year`, whose edge leaks with `half_life`."""
    class Venturing(Diffusion):
        def knowledge_half_life_years(self, country=None):
            return half_life
    return module_harness.build(Venturing, views={
        "operating": lambda: set(operating), "tree": nodes.get, "done_year": lambda: {}, "year": year,
        "venture_opened_year": lambda node_id, default: opened_year}, world=DiffusionWorld())


class Spreading(unittest.TestCase):
    NODES = {"mill": {"rev": 300.0}, "stall": {"rev": 100.0}, "shrine": {"rev": 0.0}}

    def test_a_technique_not_operating_has_nothing_to_leak(self):
        self.assertEqual(venturing([], self.NODES).diffusion_share("mill"), 0.0)

    def test_a_concern_with_no_revenue_has_no_market_to_leak_into(self):
        self.assertEqual(venturing(["shrine"], self.NODES).diffusion_share("shrine"), 0.0)

    def test_one_half_life_after_opening_half_the_edge_has_leaked(self):
        self.assertAlmostEqual(venturing(["mill"], self.NODES, opened_year=80, half_life=20.0).diffusion_share("mill"), 0.5)

    def test_a_shorter_half_life_leaks_more_by_the_same_age_but_never_past_the_cap(self):
        slow = venturing(["mill"], self.NODES, half_life=40.0).diffusion_share("mill")
        fast = venturing(["mill"], self.NODES, half_life=5.0).diffusion_share("mill")
        self.assertLess(slow, fast)
        self.assertEqual(fast, constants.VENTURE_DIFFUSION_CAP)

    def test_a_concern_opened_this_year_has_leaked_nothing(self):
        self.assertEqual(venturing(["mill"], self.NODES, opened_year=100).diffusion_share("mill"), 0.0)

    def test_the_index_is_the_revenue_weighted_average_of_what_each_has_leaked(self):
        module = venturing(["mill", "stall"], self.NODES)
        shares = {"mill": 0.6, "stall": 0.2}
        module.diffusion_share = shares.get
        self.assertAlmostEqual(module.venture_diffusion_index(), (300.0 * 0.6 + 100.0 * 0.2) / 400.0)

    def test_the_index_is_zero_with_nothing_earning_operating(self):
        self.assertEqual(venturing(["shrine"], self.NODES).venture_diffusion_index(), 0.0)
        self.assertEqual(venturing([], self.NODES).venture_diffusion_index(), 0.0)


if __name__ == "__main__":
    unittest.main()
