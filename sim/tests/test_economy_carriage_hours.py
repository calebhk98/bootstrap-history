"""Carriage is hired labour (Complaints/552): a merchant bids for the crew hours its shipments need in the
year's labour market, before the goods move; what is hired limits what is carried, and the money still adds up."""

import unittest
from unittest import mock

from sim.economy import carriage_hours, economy, merchants, money_audit
from sim.economy.merchants import CrewHire, Merchant
from sim.economy.types import Fill
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_merchants import SPECS, merchant, plan, world

CREW_HOURS_PER_TONNE_KM = 0.05
CART_RATE = 0.12                 # dear enough that the fixture's tiles trade ore now and then


def trading_setup(crew=True):
    rates = {"cart": CART_RATE, "pack": 2 * CART_RATE, "sail": CART_RATE / 4}
    crew_modes = {"cart": (fixture.LABOURER, CREW_HOURS_PER_TONNE_KM)} if crew else {}
    return fixture.small_setup(carriage_rates=rates, carriage_crew=crew_modes)


def run_watching(setup, years):
    """Run the fixture economy; return it and, per year, what the merchants wanted and were hired for just
    before they dispatched, with the hours the labour market gave to every other employer of the trade."""
    watched = []
    real = economy.dispatch_merchants

    def watch(setup_, record, carriage, ledger):
        trade = fixture.LABOURER
        before = {each.agent_id: dict(each.carriage_hours_wanted or {}) for each in record.merchants.values()}
        hired = {agent: carriage_hours.hired(ledger, agent, [trade]) for agent in record.merchants}
        real(setup_, record, carriage, ledger)
        after = {each.agent_id: dict(each.carriage_hours_wanted or {}) for each in record.merchants.values()}
        market = sum(hours for key, hours in record.hours_hired.items() if key.startswith(trade + "|"))
        others = market - sum(each["hours"] for each in hired.values())
        watched.append({"planned": before, "hired": hired, "wanted_after": after, "others_hired": others})
    with mock.patch.object(economy, "dispatch_merchants", watch):
        done, _outcomes = fixture.run(setup, years)
    return done, watched


class CarriageHireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hiring_economy, cls.hiring = run_watching(trading_setup(), 20)
        _plain, cls.plain = run_watching(trading_setup(crew=False), 20)

    def planned_years(self):
        return [year for year in self.hiring
                if any(sum(plan_.values()) > 0.0 for plan_ in year["planned"].values())]

    def test_the_merchants_shipments_are_planned_in_hours(self):
        self.assertTrue(self.planned_years(), "no merchant shipped, so the scenario shows nothing")

    def test_the_carrier_trade_hires_hours_for_the_plan_and_no_more(self):
        for year in self.planned_years():
            for agent, plan_ in year["planned"].items():
                hours = year["hired"][agent]["hours"]
                self.assertGreater(hours, 0.0)
                self.assertLessEqual(hours, sum(plan_.values()) + 1e-9)

    def test_a_plan_the_market_can_fill_is_hired_in_full(self):
        full = [year for year in self.planned_years()
                if all(abs(year["hired"][agent]["hours"] - sum(plan_.values())) < 1e-6
                       for agent, plan_ in year["planned"].items() if sum(plan_.values()) > 0.0)]
        self.assertTrue(full)

    def test_hired_carriers_are_paid_the_labour_markets_wage(self):
        for year in self.planned_years():
            for agent, plan_ in year["planned"].items():
                if sum(plan_.values()) > 0.0:
                    self.assertGreater(year["hired"][agent]["wage"], 0.0)

    def test_hours_given_to_carriage_are_taken_from_what_other_employers_hire(self):
        index = self.hiring.index(self.planned_years()[0])   # the two runs are alike until the first bid
        self.assertLess(self.hiring[index]["others_hired"], self.plain[index]["others_hired"])

    def test_money_is_still_conserved(self):
        report = money_audit.year_report(self.hiring_economy.record)
        self.assertTrue(report.ok, report.unexpected)
        self.assertAlmostEqual(self.hiring_economy.record.book.check_conservation(1e-9).money["coin"], 0.0)


class ShortfallTests(unittest.TestCase):
    def ship(self, hired_hours):
        carriage, _m, area_a, _b = world()
        who = merchant()
        plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        return merchants.dispatch(who, fills, carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0},
                                  crew=CrewHire(hours_per_money=0.5, hours_hired=hired_hours, wage=1.0))

    def test_carriers_enough_for_every_unit_carry_all_of_it_and_the_fee_less_their_wages_is_left_to_pay(self):
        result = self.ship(5.0)       # ten units cost ten in carriage, five hours of crew at one an hour
        self.assertAlmostEqual(result.moves[0].quantity, 10.0)
        self.assertAlmostEqual(result.transfers[0].amount, 10.0 - 5.0)

    def test_half_the_carriers_carry_half_the_goods(self):
        result = self.ship(2.5)
        self.assertAlmostEqual(result.moves[0].quantity, 5.0)
        self.assertAlmostEqual(result.stranded[0][2], 5.0)

    def test_no_carriers_carry_nothing(self):
        result = self.ship(0.0)
        self.assertEqual(result.moves, ())

    def test_every_route_is_cut_by_the_same_share(self):
        carriage, _m, _a, _b = world(("salt", "fish"))
        who = merchant()
        who.routes = {("salt", "a"): ("b", "x"), ("fish", "a"): ("b", "x")}
        result = merchants.dispatch(who, (), carriage, SPECS, "coin", 100.0,
                                    {("salt", "a"): 10.0, ("fish", "a"): 4.0},
                                    crew=CrewHire(hours_per_money=0.5, hours_hired=3.5, wage=1.0))
        carried = {move.good: move.quantity for move in result.moves}
        self.assertAlmostEqual(carried["salt"], 5.0)
        self.assertAlmostEqual(carried["fish"], 2.0)

    def test_hours_wanted_are_reported_before_any_cut(self):
        self.assertAlmostEqual(self.ship(2.5).crew_hours_wanted["a"], 5.0)


class CrewTests(unittest.TestCase):
    def test_a_setup_naming_no_crew_hires_none(self):
        self.assertIsNone(carriage_hours.crew_of(trading_setup(crew=False)))

    def test_crew_hours_per_money_are_the_modes_hours_over_its_money_rate(self):
        crew = carriage_hours.crew_of(trading_setup())
        self.assertEqual(crew.trades, ((fixture.LABOURER, 1.0),))
        self.assertAlmostEqual(crew.hours_per_money, CREW_HOURS_PER_TONNE_KM / CART_RATE)

    def test_the_modes_own_crew_trade_is_not_hired_while_carriage_is_bid_in_the_unskilled_trade(self):
        setup = fixture.small_setup(carriage_rates={"cart": CART_RATE}, carriage_crew={"cart": ("carter", 0.1)})
        self.assertEqual(carriage_hours.crew_of(setup).trades, ((fixture.LABOURER, 1.0),))
        with mock.patch.object(carriage_hours, "CARRIAGE_CREW_UNSKILLED_SHARE", 0.25):
            self.assertEqual(carriage_hours.crew_of(setup).trades, (("carter", 0.75), (fixture.LABOURER, 0.25)))

    def test_a_merchant_that_shipped_nothing_has_no_plan_and_bids_nothing(self):
        record = type("Record", (), {"merchants": {"m": Merchant("m", "a", "owner", 1.0)}, "cohorts": {}})()
        self.assertFalse(carriage_hours.planned(record.merchants["m"]))
        self.assertEqual(carriage_hours.bids(trading_setup(), record), [])


class BidAreaTests(unittest.TestCase):
    def bids(self, populated_tiles):
        who = Merchant("m1", "town", "owner", 1.0)
        who.carriage_hours_wanted = {"hills": 40.0, "farms": 10.0}
        cohorts = {tile: type("Cohort", (), {"tile": tile})() for tile in populated_tiles}
        record = type("Record", (), {"merchants": {"m1": who}, "cohorts": cohorts})()
        return {bid.area: bid.hours for bid in carriage_hours.bids(trading_setup(), record)}

    def test_carriers_are_bid_for_where_the_goods_left_when_people_live_there(self):
        self.assertEqual(self.bids(["town", "farms", "hills"]), {"work@hills": 40.0, "work@farms": 10.0})

    def test_where_nobody_lives_the_bid_is_placed_where_the_merchant_lives(self):
        self.assertEqual(self.bids(["town", "farms"]), {"work@town": 40.0, "work@farms": 10.0})


class WageLoanTests(unittest.TestCase):
    """Carriers are paid at the labour market, before lenders meet, so a merchant short of cash borrows its wage bill."""

    def record(self, cash):
        from sim.economy.accounts import Book
        from sim.economy.market_memory import market_key
        from sim.economy.setup import labour_area
        from sim.economy.types import EDGE_MINT, Transfer
        book = Book()
        if cash > 0.0:
            book.transfer(Transfer(EDGE_MINT, "m1", "coin", cash, "opening"))
        who = Merchant("m1", "town", "owner", 100.0)
        who.carriage_hours_wanted = {"town": 100.0}
        memory = type("Memory", (), {"wages": {market_key(fixture.LABOURER, labour_area("town")): 0.5}})()
        return type("Record", (), {"merchants": {"m1": who}, "book": book, "memory": memory})()

    def test_a_merchant_without_cash_borrows_the_whole_wage_bill_for_a_year(self):
        setup = trading_setup()
        asked = carriage_hours.wage_loans(setup, self.record(0.0), carriage_hours.crew_of(setup))
        self.assertEqual(len(asked), 1)
        self.assertAlmostEqual(asked[0].amount, 100.0 * 0.5)
        self.assertEqual((asked[0].borrower, asked[0].years), ("m1", 1.0))

    def test_a_merchant_borrows_only_what_its_cash_does_not_cover(self):
        setup = trading_setup()
        asked = carriage_hours.wage_loans(setup, self.record(20.0), carriage_hours.crew_of(setup))
        self.assertAlmostEqual(asked[0].amount, 30.0)

    def test_a_merchant_with_cash_enough_asks_for_nothing(self):
        setup = trading_setup()
        self.assertEqual(carriage_hours.wage_loans(setup, self.record(80.0), carriage_hours.crew_of(setup)), [])


if __name__ == "__main__":
    unittest.main()
