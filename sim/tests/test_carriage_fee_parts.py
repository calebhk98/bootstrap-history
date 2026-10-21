"""Complaint 632: the parts of a carriage fee go to those who supply them. The crew is paid by the labour market, the
carriers worn and the feed the animals eat are bought in the goods market, and the rest stays with the merchant that
owns the carriers; none of it is paid to the poorest households of the source tile."""
import dataclasses
import unittest
from unittest import mock

from sim.economy import carriage_fleet_book, carriage_hours, carriage_wear, economy, merchants, money_audit
from sim.economy.types import Fill
from sim.tests import economy_fixture as fixture
from sim.tests import test_carriage_wear as wear_fixture
from sim.tests import test_economy_merchants as basic

FEED_GOOD = fixture.GRAIN
FEED_KG_PER_TONNE_KM = 1.0


class FeedIsARowOfTheTable(unittest.TestCase):
    TEAM = {"cart": {"carriers": [["animal", "ox", 2.0], ["vehicle", "cart", 1.0]], "tonne_km_per_team_day": 20.0,
                     "team_payload_tonnes": 1.0, "animal_feed_kg_per_tonne_km": 1.5}}
    USES = {"cart": {"serves": {"vehicle": "cart"}, "days_per_year": 150.0}}

    def test_a_team_with_animals_uses_up_feed_by_the_tonne_km(self):
        found = carriage_wear.table(self.TEAM, self.USES, {"cart": 10.0}, ("wheat", 2.0))
        rows = dict(found["cart"][1])
        self.assertAlmostEqual(rows["wheat"], 1.5 / 2.0)       # units of the feed good, whose unit is 2 kg
        self.assertIn("cart", rows)

    def test_a_team_without_animals_eats_nothing(self):
        team = {"sail": dict(self.TEAM["cart"], carriers=[["vehicle", "cart", 1.0]], animal_feed_kg_per_tonne_km=0.0)}
        rows = dict(carriage_wear.table(team, self.USES, {"cart": 10.0}, ("wheat", 2.0))["sail"][1])
        self.assertNotIn("wheat", rows)

    def test_no_feed_good_means_no_feed_row(self):
        rows = dict(carriage_wear.table(self.TEAM, self.USES, {"cart": 10.0})["cart"][1])
        self.assertEqual(list(rows), ["cart"])


class WhatIsLeftOfAFee(unittest.TestCase):
    def dispatch(self, cash=100.0, **kwargs):
        carriage, _map, area_a, _b = basic.world()
        who = basic.merchant()
        basic.plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        return merchants.dispatch(who, fills, carriage, basic.SPECS, "coin", cash, {("salt", "a"): 10.0},
                                  carrier_of={"a": "the poorest of a"}.get, **kwargs)

    def test_without_a_decomposed_fee_the_poorest_are_paid_as_before(self):
        result = self.dispatch()
        self.assertEqual([each.payee for each in result.transfers], ["the poorest of a"])

    def test_the_part_the_merchant_buys_is_not_paid_to_the_poorest(self):
        result = self.dispatch(carrier_money=lambda source, destination: 0.4, margin_kept=True)
        self.assertEqual(result.transfers, ())

    def test_the_part_the_merchant_buys_is_taken_off_the_fee_when_the_margin_is_not_kept(self):
        result = self.dispatch(carrier_money=lambda source, destination: 0.4)
        self.assertAlmostEqual(result.transfers[0].amount, 10.0 * (basic.CARRIAGE_PER_UNIT - 0.4))

    def test_the_margin_is_not_a_cash_need_so_a_poor_merchant_still_ships(self):
        result = self.dispatch(cash=0.0, carrier_money=lambda source, destination: 0.4, margin_kept=True)
        self.assertAlmostEqual(result.moves[0].quantity, 10.0)
        self.assertEqual(result.stranded, ())


class FeedCrewAndCartsAreBought(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = wear_fixture.carrying_setup()
        rows = dict(base.carriage_carriers)["cart"][1] + ((FEED_GOOD, FEED_KG_PER_TONNE_KM),)
        cls.setup = dataclasses.replace(
            base, carriage_carriers={"cart": (wear_fixture.CART_TONNE_KM_PER_TEAM_DAY, rows)})
        cls.years = []
        real_dispatch = merchants.dispatch
        real_close = economy.dispatch_merchants

        def watch_dispatch(merchant, *args, **kwargs):
            done = real_dispatch(merchant, *args, **kwargs)
            cls.years[-1]["planned"][merchant.agent_id] = carriage_hours.planned(merchant)
            cls.years[-1]["payees"].extend((merchant.agent_id, each.payee, each.amount) for each in done.transfers)
            return done

        def watch_close(setup, record, carriage, ledger, area_map):
            cls.years.append({"planned": {}, "payees": []})
            real_close(setup, record, carriage, ledger, area_map)
            cls.years[-1]["eaten"] = {each.agent_id: each.carrier_wear.get(FEED_GOOD, 0.0) for each in record.merchants.values()}
            cls.years[-1]["worn_carts"] = {each.agent_id: each.carrier_wear.get(wear_fixture.CART, 0.0) for each in record.merchants.values()}
        with mock.patch.object(economy, "dispatch_merchants", watch_close), \
                mock.patch.object(merchants, "dispatch", watch_dispatch):
            cls.economy, cls.outcomes = fixture.run(cls.setup, 25)

    def shipping_years(self):
        return [year for year in self.years if any(units > 0.0 for units in year["eaten"].values())]

    def test_the_animals_feed_is_used_up_by_the_tonne_km_shipped(self):
        self.assertTrue(self.shipping_years(), "no merchant shipped, so the scenario shows nothing")

    def test_the_carts_worn_are_still_bought_alongside_the_feed(self):
        self.assertTrue(any(units > 0.0 for year in self.years for units in year["worn_carts"].values()))

    def test_merchants_bid_for_feed_in_the_goods_market(self):
        record = self.economy.record
        merchant = next(iter(record.merchants.values()))
        merchant.carrier_wear = {FEED_GOOD: 3.0}
        bids, budget = carriage_fleet_book.bids(self.setup, record, self.economy.view(), self.economy.area_map)
        mine = [bid for bid in bids if bid.buyer == merchant.agent_id and bid.good == FEED_GOOD]
        self.assertEqual(len(mine), 1)
        self.assertAlmostEqual(mine[0].floor_quantity, 3.0)
        self.assertGreater(budget[merchant.agent_id], 0.0)

    def test_nothing_is_paid_to_the_poorest_for_supplies_they_did_not_make(self):
        self.assertTrue(any(planned for year in self.years for planned in year["planned"].values()), "no merchant had a plan")
        for year in self.years:
            for agent, payee, amount in year["payees"]:
                if year["planned"].get(agent):      # a merchant with a plan hired its crew; the rest is not paid out
                    self.assertAlmostEqual(amount, 0.0, msg=(agent, payee))

    def test_money_is_conserved(self):
        report = money_audit.year_report(self.economy.record)
        self.assertTrue(report.ok, report.unexpected)


if __name__ == "__main__":
    unittest.main()
