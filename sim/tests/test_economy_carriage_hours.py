"""Carriage is hired labour (Complaints/552): a merchant bids for the crew hours its shipments need in the
year's labour market, before the goods move; what is hired limits what is carried, and the money still adds up."""

import unittest
from unittest import mock

from sim.economy import carriage_hours, economy, merchants, money_audit
from sim.economy.merchants import CrewHire, Merchant
from sim.economy.market_memory import market_key
from sim.economy.types import Fill
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_merchants import SPECS, merchant, plan, world

CREW_HOURS_PER_TONNE_KM = 0.05
CART_RATE = 0.12                 # dear enough that the fixture's tiles trade ore now and then


def trading_setup(crew=True, carriage_wage=0.0):
    rates = {"cart": CART_RATE, "pack": 2 * CART_RATE, "sail": CART_RATE / 4}
    crew_modes = {"cart": (fixture.LABOURER, CREW_HOURS_PER_TONNE_KM)} if crew else {}
    return fixture.small_setup(carriage_rates=rates, carriage_crew=crew_modes, carriage_wage=carriage_wage)


def run_watching(setup, years):
    """Run the fixture economy; return it and, per year, what the merchants wanted and were hired for just
    before they dispatched, with the hours the labour market gave to every other employer of the trade."""
    watched = []
    real = economy.dispatch_merchants

    def watch(setup_, record, carriage, ledger, area_map):
        trade = fixture.LABOURER
        before = {each.agent_id: dict(each.carriage_hours_wanted or {}) for each in record.merchants.values()}
        hired = {agent: carriage_hours.hired(ledger, agent, [trade]) for agent in record.merchants}
        real(setup_, record, carriage, ledger, area_map)
        after = {each.agent_id: dict(each.carriage_hours_wanted or {}) for each in record.merchants.values()}
        market = sum(hours for key, hours in record.hours_hired.items() if key.startswith(trade + "|"))
        others = market - sum(each["hours"] for each in hired.values())
        watched.append({"planned": before, "hired": hired, "wanted_after": after, "others_hired": others})
    with mock.patch.object(economy, "dispatch_merchants", watch), fixture.surplus_households():   # goods are carried out of a surplus
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
        # a year can hire nothing (see EntrantInAHeldMarketTests); what is hired never passes the plan
        for year in self.planned_years():
            for agent, plan_ in year["planned"].items():
                self.assertLessEqual(year["hired"][agent]["hours"], sum(plan_.values()) + 1e-9)

    def test_some_planned_year_hires_carriers(self):
        self.assertTrue(any(year["hired"][agent]["hours"] > 0.0
                            for year in self.planned_years() for agent in year["planned"]))

    def test_a_plan_the_market_can_fill_is_hired_in_full(self):
        full = [year for year in self.planned_years()
                if all(abs(year["hired"][agent]["hours"] - sum(plan_.values())) < 1e-6
                       for agent, plan_ in year["planned"].items() if sum(plan_.values()) > 0.0)]
        self.assertTrue(full)

    def test_hired_carriers_are_paid_the_labour_markets_wage(self):
        for year in self.hiring:
            for hire_ in year["hired"].values():
                if hire_["hours"] > 0.0:
                    self.assertGreater(hire_["wage"], 0.0)

    def test_money_is_still_conserved(self):
        report = money_audit.year_report(self.hiring_economy.record)
        self.assertTrue(report.ok, report.unexpected)
        self.assertAlmostEqual(self.hiring_economy.record.book.check_conservation(1e-9).money["coin"], 0.0)


class EntrantInAHeldMarketTests(unittest.TestCase):
    def test_a_merchant_with_no_hires_gets_none_where_incumbents_hold_all_the_hours_at_the_same_pay(self):
        from sim.tests.test_labour_core_clearing import bid, make_state, run
        state = make_state(people=10.0, wage=1.0)
        state.hired_hours = {"vale": {"digger": {"farm": 1000.0}}}
        result = run(state, [bid("farm", 2000.0), bid("merchant", 50.0)])
        self.assertEqual(result.hired_by_employer.get("merchant", 0.0), 0.0)

    def test_the_same_merchant_paying_a_premium_takes_hours_from_the_incumbent(self):
        from sim.tests.test_labour_core_clearing import bid, make_state, run
        state = make_state(people=10.0, wage=1.0)
        state.hired_hours = {"vale": {"digger": {"farm": 1000.0}}}
        result = run(state, [bid("farm", 2000.0), bid("merchant", 50.0, premium=0.5)])
        self.assertGreater(result.hired_by_employer.get("merchant", 0.0), 0.0)


def hours_hired_by_farm(merchant_bid_hours):
    """Hours the farm is hired for in a labour market of scarce supply, when a merchant also bids `merchant_bid_hours`
    for its carriers at a higher wage; the bids go through the year's labour clearing together."""
    import types
    from sim.economy.accounts import Book
    from sim.economy.market_memory import MarketMemory
    from sim.economy.types import EDGE_MINT, LabourBid, LabourOffer, Transfer
    from sim.economy.year_labour import clear_labour
    from sim.economy.year_ledger import YearLedger
    from sim.labour.api import MarketState, YearInputs as CoreInputs
    from sim.labour.market.aptitude import split_evenly
    book = Book()
    for employer in ("farm", "merchant"):
        book.transfer(Transfer(EDGE_MINT, employer, "coin", 1e9, "opening"))
    area = "labour:t1"
    record = types.SimpleNamespace(book=book, memory=MarketMemory(),
                                   workforce=MarketState(workers={area: {"plough": split_evenly(0.05)}}))
    setup = types.SimpleNamespace(currency_id="coin", trades={}, unskilled_trade="plough")
    bids = [LabourBid("farm", "plough", area, 100.0, 5.0)]
    if merchant_bid_hours:
        bids.append(LabourBid("merchant", "plough", area, merchant_bid_hours, 9.0))
    ledger = YearLedger()
    context = CoreInputs(trades={}, bids=(), subsistence_per_worker_year={area: 2000.0},
                         hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0)
    clear_labour(setup, record, bids, [LabourOffer("family", "plough", area, 100.0, 1.0)], ledger, context)
    return ledger.hours_hired.get("farm", {}).get("plough", 0.0), ledger.hours_hired.get("merchant", {}).get("plough", 0.0)


class CarriageTakesHoursTests(unittest.TestCase):
    def test_hours_given_to_carriage_are_taken_from_what_other_employers_hire(self):
        farm_alone, _none = hours_hired_by_farm(0.0)
        farm_with_carriers, carriers = hours_hired_by_farm(40.0)
        self.assertGreater(carriers, 0.0)
        self.assertLess(farm_with_carriers, farm_alone)


def hire(hours_hired, hours_per_unit=0.5, wage=1.0, market_wage=1.0, area_of=None):
    """Crew of one trade hired at tile a: each tonne needs `hours_per_unit` hours, of which `hours_hired` were bought."""
    key = market_key(fixture.LABOURER, "a")
    return CrewHire(lambda _source, _destination: ((key, hours_per_unit),), {key: hours_hired}, {key: wage},
                    lambda _key: market_wage, area_of or (lambda _good, tile: "area_" + tile))


class ShortfallTests(unittest.TestCase):
    def ship(self, hired_hours):
        carriage, _m, area_a, _b = world()
        who = merchant()
        plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        return merchants.dispatch(who, fills, carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0},
                                  crew=hire(hired_hours))

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
                                    crew=hire(3.5))
        carried = {move.good: move.quantity for move in result.moves}
        self.assertAlmostEqual(carried["salt"], 5.0)
        self.assertAlmostEqual(carried["fish"], 2.0)

    def test_hours_wanted_are_reported_before_any_cut(self):
        self.assertAlmostEqual(self.ship(2.5).crew_hours_wanted[market_key(fixture.LABOURER, "a")], 5.0)


class CrewWorthTests(unittest.TestCase):
    """An hour of crew is worth to a merchant the haul's gain (destination price less origin price, less the part
    of the fee that is not crew pay) over the hours; the whole fee over the hours would lift the labour wage far
    above what the carriage pays a driver."""

    def want(self, price_at_source, price_at_destination, market_wage=0.2):
        carriage, _m, area_a, area_b = world()
        who = merchant()
        plan(who, price_at_source, price_at_destination)
        who.routes = {("salt", "a"): ("b", area_b["salt"])}
        crew = hire(100.0, market_wage=market_wage, area_of=lambda _good, tile: area_a["salt"] if tile == "a" else "elsewhere")
        return merchants.dispatch(who, (), carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0}, crew=crew)

    def test_a_wide_spread_is_worth_the_gain_over_the_hours(self):
        key = market_key(fixture.LABOURER, "a")
        result = self.want(2.0, 5.0)    # ten units: a gain of 3 each less 0.9 of the fee that is not crew pay (0.5 hours at 0.2 is 0.1 of 1), over 5 hours
        self.assertAlmostEqual(result.crew_money_wanted[key] / result.crew_hours_wanted[key], (3.0 - 0.9) * 10.0 / 5.0)

    def test_it_is_not_the_whole_fee_over_the_hours(self):
        key = market_key(fixture.LABOURER, "a")
        result = self.want(2.0, 5.0)
        self.assertNotAlmostEqual(result.crew_money_wanted[key] / result.crew_hours_wanted[key], 10.0 / 5.0)

    def test_a_spread_below_the_fee_that_is_not_crew_pay_is_worth_nothing(self):
        key = market_key(fixture.LABOURER, "a")
        result = self.want(2.0, 2.5)
        self.assertEqual(result.crew_money_wanted[key], 0.0)
        self.assertGreater(result.crew_hours_wanted[key], 0.0)


class CrewTests(unittest.TestCase):
    def test_a_setup_naming_no_crew_hires_none(self):
        setup = trading_setup(crew=False)
        self.assertFalse(carriage_hours.hires(setup))
        self.assertIsNone(carriage_hours.crew_for(setup, type("Record", (), {"area_imbalance": 1.0})(), setup.carriage_table()))

    def test_a_haul_needs_the_modes_crew_hours_over_the_tonne_km_its_money_stands_for(self):
        setup = trading_setup()
        carriage = setup.carriage_table()
        hours = carriage_hours.Crew(setup, carriage, 1.0).hours_by_trade(fixture.TOWN, fixture.FARMS)
        fee = carriage.cost_per_tonne(fixture.TOWN, fixture.FARMS)
        self.assertEqual(list(hours), [fixture.LABOURER])
        self.assertAlmostEqual(hours[fixture.LABOURER], fee / CART_RATE * CREW_HOURS_PER_TONNE_KM * 2.0)   # carriers return empty: two legs of crew

    def test_the_modes_own_crew_trade_is_not_hired_while_carriage_is_bid_in_the_unskilled_trade(self):
        setup = fixture.small_setup(carriage_rates={"cart": CART_RATE}, carriage_crew={"cart": ("carter", 0.1)})
        self.assertEqual(carriage_hours.crew_trades(setup, "carter"), ((fixture.LABOURER, 1.0),))
        with mock.patch.object(carriage_hours, "CARRIAGE_CREW_UNSKILLED_SHARE", 0.25):
            self.assertEqual(carriage_hours.crew_trades(setup, "carter"), (("carter", 0.75), (fixture.LABOURER, 0.25)))

    def test_a_merchant_that_shipped_nothing_has_no_plan_and_bids_nothing(self):
        record = type("Record", (), {"merchants": {"m": Merchant("m", "a", "owner", 1.0)}, "cohorts": {}, "area_imbalance": 1.0})()
        self.assertFalse(carriage_hours.planned(record.merchants["m"]))
        self.assertEqual(carriage_hours.bids(trading_setup(), record), [])


class OneWageTests(unittest.TestCase):
    """The carriage rates were priced at the opening wage; the labour part of a fee follows the market wage the
    crew is paid at the area the goods leave, so the crew's pay is that labour part."""

    def priced(self, market_wage, wage_elsewhere=None):
        from sim.economy.setup import labour_area
        setup = trading_setup(carriage_wage=1.0)
        wages = {market_key(fixture.LABOURER, labour_area(tile)): market_wage for tile in fixture.tiles()}
        if wage_elsewhere is not None:
            wages.update({market_key(fixture.LABOURER, labour_area(tile)): wage_elsewhere
                          for tile in fixture.tiles() if tile != fixture.TOWN})
        carried = {fixture.TOWN: {fixture.FARMS: 10.0}}
        record = type("Record", (), {"memory": type("Memory", (), {"wages": wages})(), "carried": carried,
                                     "area_imbalance": 1.0})()
        table = setup.carriage_table()
        scale = carriage_hours.wage_scale(setup, record, table)
        base = setup.carriage_table().cost_per_tonne(fixture.TOWN, fixture.FARMS)
        table.set_scale(scale)
        fee = table.cost_per_tonne(fixture.TOWN, fixture.FARMS)
        hours_needed = carriage_hours.Crew(setup, table, 1.0).hours_by_trade(fixture.TOWN, fixture.FARMS)[fixture.LABOURER]
        return scale, base, fee, hours_needed * market_wage

    def test_wages_unchanged_leave_the_table_exactly_as_priced(self):
        scale, base, fee, _pay = self.priced(1.0)
        self.assertEqual((scale, fee), (1.0, base))

    def test_when_the_market_wage_halves_the_labour_part_of_a_fee_halves(self):
        _scale, base, fee, pay = self.priced(1.0)
        _scale, _base, cheaper_fee, cheaper_pay = self.priced(0.5)
        self.assertAlmostEqual(cheaper_pay, pay / 2.0)
        self.assertAlmostEqual(fee - pay, cheaper_fee - cheaper_pay)      # feed, carts and animals keep their price

    def test_the_crews_pay_is_the_labour_part_of_the_fee(self):
        _scale, base, _fee, pay = self.priced(0.5)
        labour_share = CREW_HOURS_PER_TONNE_KM * 2.0 * 1.0 / CART_RATE      # of a fee priced at the opening wage
        self.assertAlmostEqual(pay, base * labour_share * 0.5)

    def test_the_wage_of_the_area_the_goods_leave_sets_the_scale_not_another_areas(self):
        self.assertEqual(self.priced(1.0, wage_elsewhere=3.0)[0], 1.0)
        self.assertLess(self.priced(0.5, wage_elsewhere=3.0)[0], 1.0)

    def test_a_wage_far_below_the_priced_wage_never_makes_carriage_pay_the_shipper(self):
        scales = []
        original = carriage_hours.wage_scale
        with mock.patch.object(carriage_hours, "wage_scale", lambda *args: scales.append(original(*args)) or scales[-1]):
            run_watching(trading_setup(carriage_wage=3.0), 20)
        self.assertTrue(scales)
        self.assertGreaterEqual(min(scales), 0.0)

    def test_money_still_balances_when_the_market_wage_differs_from_the_priced_wage(self):
        done, _years = run_watching(trading_setup(carriage_wage=3.0), 20)
        self.assertTrue(money_audit.year_report(done.record).ok)


class LoanTimingTests(unittest.TestCase):
    def test_the_wage_loan_is_sized_on_the_cash_left_after_the_owners_took_their_profit(self):
        seen = []
        real = economy.close_agents

        def watch(setup, record, view, ledger, area_map, *rest):
            before = len(record.loan_requests)
            for each in record.merchants.values():
                if carriage_hours.planned(each):
                    each.capital_base = 0.0     # all its cash is profit, which goes to the owner at the close
            real(setup, record, view, ledger, area_map, *rest)
            asked = {request.borrower: request.amount for request in record.loan_requests[before:]
                     if request.borrower in record.merchants}
            wanted = {request.borrower: request.amount for request in carriage_hours.wage_loans(setup, record)}
            seen.append((asked, wanted))
        with mock.patch.object(economy, "close_agents", watch), fixture.surplus_households():
            fixture.run(trading_setup(), 20)
        self.assertTrue(any(wanted for _asked, wanted in seen), "no merchant needed a loan, so the scenario shows nothing")
        for asked, wanted in seen:
            self.assertEqual(asked, wanted)


class BidAreaTests(unittest.TestCase):
    def bids(self, populated_tiles):
        who = Merchant("m1", "town", "owner", 1.0)
        who.carriage_hours_wanted = {market_key(fixture.LABOURER, "hills"): 40.0, market_key(fixture.LABOURER, "farms"): 10.0}
        cohorts = {tile: type("Cohort", (), {"tile": tile})() for tile in populated_tiles}
        record = type("Record", (), {"merchants": {"m1": who}, "cohorts": cohorts, "area_imbalance": 1.0})()
        return {bid.area: bid.hours for bid in carriage_hours.bids(trading_setup(), record) if bid.trade == fixture.LABOURER}

    def test_carriers_are_bid_for_where_the_goods_left_when_people_live_there(self):
        self.assertEqual(self.bids(["town", "farms", "hills"]), {"work@hills": 40.0, "work@farms": 10.0})

    def test_where_nobody_lives_the_bid_is_placed_where_the_merchant_lives(self):
        self.assertEqual(self.bids(["town", "farms"]), {"work@town": 40.0, "work@farms": 10.0})


class BidMaximumTests(unittest.TestCase):
    def test_the_maximum_bid_for_an_hour_is_the_carriage_money_the_hour_stands_for(self):
        key = market_key(fixture.LABOURER, "farms")
        who = Merchant("m1", "town", "owner", 1.0)
        who.carriage_hours_wanted = {key: 40.0}
        who.carriage_money_wanted = {key: 90.0}
        cohorts = {tile: type("Cohort", (), {"tile": tile})() for tile in ("town", "farms")}
        record = type("Record", (), {"merchants": {"m1": who}, "cohorts": cohorts, "area_imbalance": 1.0})()
        found = carriage_hours.bids(trading_setup(), record)
        self.assertEqual([bid.maximum_wage for bid in found], [90.0 / 40.0])


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
        who.carriage_hours_wanted = {market_key(fixture.LABOURER, "town"): 100.0}
        who.carriage_money_wanted = {market_key(fixture.LABOURER, "town"): 100.0}
        memory = type("Memory", (), {"wages": {market_key(fixture.LABOURER, labour_area("town")): 0.5}})()
        cohorts = {"town": type("Cohort", (), {"tile": "town"})()}
        return type("Record", (), {"merchants": {"m1": who}, "book": book, "memory": memory, "cohorts": cohorts})()

    def test_a_merchant_without_cash_borrows_the_whole_wage_bill_for_a_year(self):
        setup = trading_setup()
        asked = carriage_hours.wage_loans(setup, self.record(0.0))
        self.assertEqual(len(asked), 1)
        self.assertAlmostEqual(asked[0].amount, 100.0 * 0.5)
        self.assertEqual((asked[0].borrower, asked[0].years), ("m1", 1.0))

    def test_a_merchant_borrows_only_what_its_cash_does_not_cover(self):
        setup = trading_setup()
        asked = carriage_hours.wage_loans(setup, self.record(20.0))
        self.assertAlmostEqual(asked[0].amount, 30.0)

    def test_the_wage_loan_covers_only_the_hours_the_market_gave_it_last_year(self):
        # Complaint 473: bids for far more hours than the area's people offer clear at a high wage, and a loan
        # for the whole bid at that wage would draw every household's spare cash.
        setup = trading_setup()
        record = self.record(0.0)
        market = (fixture.LABOURER, "work@town")
        asked = carriage_hours.wage_loans(setup, record, {"m1": {market: 10.0}})
        self.assertAlmostEqual(asked[0].amount, 10.0 * 0.5)
        self.assertEqual(carriage_hours.wage_loans(setup, record, {"m1": {market: 0.0}}), [])

    def test_a_merchant_without_a_plan_is_sized_on_no_more_than_the_markets_whole_supply(self):
        market = (fixture.LABOURER, "work@town")
        asked = carriage_hours.wage_loans(trading_setup(), self.record(0.0), {}, {market: 20.0})
        self.assertAlmostEqual(asked[0].amount, 20.0 * 0.5)

    def test_a_plan_of_no_hours_asks_for_nothing(self):
        record = self.record(0.0)
        record.merchants["m1"].carriage_hours_wanted = {market_key(fixture.LABOURER, "town"): 0.0}
        self.assertEqual(carriage_hours.wage_loans(trading_setup(), record, {"m1": {}}), [])

    def test_a_merchant_with_no_crew_plan_last_year_is_sized_on_the_hours_it_wants(self):
        asked = carriage_hours.wage_loans(trading_setup(), self.record(0.0), {})
        self.assertAlmostEqual(asked[0].amount, 100.0 * 0.5)

    def test_a_merchant_with_cash_enough_asks_for_nothing(self):
        setup = trading_setup()
        self.assertEqual(carriage_hours.wage_loans(setup, self.record(80.0)), [])


if __name__ == "__main__":
    unittest.main()
