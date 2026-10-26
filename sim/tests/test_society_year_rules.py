"""The society's slow clock on stand-in games: literacy moves only where a school runs, a taught trade becomes the
society's own and grows toward its ceiling, and how much of a running concern's edge has leaked to competitors."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine.society_adoption import AdoptionMixin
from sim.engine.society_diffusion import DiffusionMixin
from sim.refusal import cause_of
from sim.tests import event_stand_in

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


class Schooling(AdoptionMixin):
    def __init__(self, flow):
        self.flow = flow
        self.literacy = Literacy()

    def effective_schooling_flow(self, field=None):
        return self.flow

    def country_literacy(self):
        return self.literacy

    def literacy_ceiling_elite(self):
        return 0.97

    def literacy_ceiling_common(self):
        return 0.9


class SchoolLiteracy(unittest.TestCase):

    def test_with_no_school_running_nothing_moves_and_nobody_is_taught(self):
        game = Schooling(0.0)
        self.assertEqual(game._school_literacy(), {})
        self.assertEqual(game.literacy.schooled, [])

    def test_a_school_moves_each_figure_toward_its_own_ceiling_at_its_rate_times_the_flow(self):
        game = Schooling(2.0)
        changed = game._school_literacy()
        self.assertEqual(game.literacy.schooled, [
            ("literacy_elite", game.LITERACY_GROWTH_RATE_ELITE * 2.0, 0.97),
            ("literacy_general", game.LITERACY_GROWTH_RATE_GENERAL * 2.0, 0.9)])
        self.assertEqual(sorted(changed), ["literacy_elite", "literacy_general"])
        self.assertLess(game.literacy.values["literacy_general"], 0.9)


class Household:
    def __init__(self, created=(), introduced=None, endemic=(), employees=None):
        self.trades_created = set(created)
        self.trade_introduced_year = dict(introduced or {})
        self.trades_endemic = set(endemic)
        self.employees = dict(employees or {})
        self.log = []


class Absorbing(AdoptionMixin):
    send = event_stand_in.send

    def __init__(self, household, flow=3.0, years_needed=50.0, ceiling=10.0):
        self.state = types.SimpleNamespace(household=household, scenario=types.SimpleNamespace(year=150))
        self.flow, self.years_needed = flow, years_needed
        self.set_to = []
        self.labour = types.SimpleNamespace(
            literate_capacity=lambda trade: ceiling, set_employed=lambda trade, count: self.set_to.append((trade, count)),
            resync_pools=lambda: None)

    def _schooling_flow(self, field=None):
        return self.flow

    def _trade_absorption_years(self, flow):
        return self.years_needed


class TradeAbsorption(unittest.TestCase):

    def test_the_first_year_a_taught_trade_is_seen_only_records_its_introduction(self):
        household = Household(created={TRADE})
        Absorbing(household)._advance_trade_absorption(100)
        self.assertEqual(household.trade_introduced_year, {TRADE: 100})
        self.assertEqual(household.trades_endemic, set())

    def test_a_trade_never_taught_here_is_left_alone(self):
        household = Household()
        Absorbing(household)._advance_trade_absorption(100)
        self.assertEqual(household.trade_introduced_year, {})

    def test_once_its_years_are_up_with_a_school_running_the_trade_becomes_the_societys_own(self):
        household = Household(created={TRADE}, introduced={TRADE: 100})
        Absorbing(household, years_needed=50.0)._advance_trade_absorption(150)
        self.assertEqual(household.trades_endemic, {TRADE})
        self.assertEqual(cause_of(household.log[0][1]), "trade_no_longer_only_yours")

    def test_before_its_years_are_up_it_is_not(self):
        household = Household(created={TRADE}, introduced={TRADE: 100})
        Absorbing(household, years_needed=50.0)._advance_trade_absorption(149)
        self.assertEqual(household.trades_endemic, set())

    def test_with_no_school_running_it_never_becomes_endemic_however_long_it_has_been(self):
        household = Household(created={TRADE}, introduced={TRADE: 0})
        Absorbing(household, flow=0.0)._advance_trade_absorption(1000)
        self.assertEqual(household.trades_endemic, set())

    def test_an_endemic_trade_grows_toward_the_same_ceiling_a_founder_hiring_is_held_to(self):
        household = Household(created={TRADE}, introduced={TRADE: 0}, endemic={TRADE}, employees={TRADE: 2.0})
        game = Absorbing(household, ceiling=12.0)
        game._advance_trade_absorption(10)
        (trade, grown), = game.set_to
        self.assertEqual(trade, TRADE)
        self.assertTrue(2.0 < grown < 12.0)

    def test_an_endemic_trade_at_its_ceiling_is_not_changed(self):
        household = Household(employees={TRADE: 12.0})
        game = Absorbing(household, ceiling=12.0)
        game._grow_endemic_trade(TRADE)
        self.assertEqual(game.set_to, [])


class Venturing(DiffusionMixin):
    VENTURE_DIFFUSION_CAP = 0.8

    def __init__(self, operating, nodes, opened_year=80, year=100, half_life=20.0):
        business = types.SimpleNamespace(opened_year_of=lambda node_id, default: opened_year)
        self.state = types.SimpleNamespace(
            projects=types.SimpleNamespace(operating=set(operating), done_year={}, business=business),
            scenario=types.SimpleNamespace(year=year))
        self.nodes = nodes
        self.half_life = half_life

    def knowledge_half_life_years(self, country=None):
        return self.half_life


class Diffusion(unittest.TestCase):
    NODES = {"mill": {"rev": 300.0}, "stall": {"rev": 100.0}, "shrine": {"rev": 0.0}}

    def test_a_technique_not_operating_has_nothing_to_leak(self):
        self.assertEqual(Venturing([], self.NODES).diffusion_share("mill"), 0.0)

    def test_a_concern_with_no_revenue_has_no_market_to_leak_into(self):
        self.assertEqual(Venturing(["shrine"], self.NODES).diffusion_share("shrine"), 0.0)

    def test_one_half_life_after_opening_half_the_edge_has_leaked(self):
        self.assertAlmostEqual(Venturing(["mill"], self.NODES, opened_year=80, half_life=20.0).diffusion_share("mill"), 0.5)

    def test_a_shorter_half_life_leaks_more_by_the_same_age_but_never_past_the_cap(self):
        slow = Venturing(["mill"], self.NODES, half_life=40.0).diffusion_share("mill")
        fast = Venturing(["mill"], self.NODES, half_life=5.0).diffusion_share("mill")
        self.assertLess(slow, fast)
        self.assertEqual(fast, 0.8)

    def test_a_concern_opened_this_year_has_leaked_nothing(self):
        self.assertEqual(Venturing(["mill"], self.NODES, opened_year=100).diffusion_share("mill"), 0.0)

    def test_the_index_is_the_revenue_weighted_average_of_what_each_has_leaked(self):
        game = Venturing(["mill", "stall"], self.NODES)
        shares = {"mill": 0.6, "stall": 0.2}
        game.diffusion_share = shares.get
        self.assertAlmostEqual(game.diffusion_index(), (300.0 * 0.6 + 100.0 * 0.2) / 400.0)

    def test_the_index_is_zero_with_nothing_earning_operating(self):
        self.assertEqual(Venturing(["shrine"], self.NODES).diffusion_index(), 0.0)
        self.assertEqual(Venturing([], self.NODES).diffusion_index(), 0.0)


if __name__ == "__main__":
    unittest.main()
