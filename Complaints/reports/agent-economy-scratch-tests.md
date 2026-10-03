# Agent economy: regression tests kept outside the suite

Written while only `sim/economy/` could change (Complaint 396). Copy each into `sim/tests/test_economy_<topic>.py` and run with `python3 sim/test_regressions.py --only economy_<topic>`. Some import fixtures from existing `sim/tests` files.

## `test_land_lease.py`

```python
"""Rent flicker: the posted rent moves a share of the way to what the tile's land clears at."""
import unittest
from types import SimpleNamespace

from sim.economy import land_market
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.producers import Producer
from sim.economy.types import EDGE_MINT, Recipe, TileSpec, Transfer
from sim.tests.test_economy_producers import View

WHEAT = Recipe("wheat", {"grain": 100.0}, {}, {"hand": 10.0})


def economy_with(hectares):
    tiles = {"t": TileSpec("t", 40.0, 0.0, hectares / 100.0, False, (), 1.0, 1.0)}
    cohorts = list(cohorts_for_tile("t", 3000.0, 0.5, 0.4))
    book = Book()
    producer = Producer("producer:t", cohort_id("t", 2), "wheat", "t", 100.0, expected_prices={"grain": 1.0})
    book.transfer(Transfer(EDGE_MINT, "producer:t", "coin", 1e9, "opening"))
    record = SimpleNamespace(producers={"producer:t": producer}, book=book,
                             cohorts={each.agent_id: each for each in cohorts}, land_rent={})
    setup = SimpleNamespace(tiles=tiles, recipes={"wheat": WHEAT}, land_per_run={"wheat": 1.0}, currency_id="coin")
    return setup, record


def view():
    return View({"grain": 1.0}, {"hand": 0.5})


def cleared_rent(setup, record, runs):
    demands = land_market.demands_of(setup, record, view(), {"producer:t": runs})
    return land_market.clear_land({"t": 100.0}, demands).rent_per_hectare_by_tile["t"]


def settle(setup, record, runs):
    land_market.settle_year(setup, record, view(), {"producer:t": runs})
    return record.land_rent["t"]


class LeaseTests(unittest.TestCase):
    def test_the_first_posting_is_what_the_land_clears_at(self):
        setup, record = economy_with(100.0)
        self.assertAlmostEqual(settle(setup, record, 300.0), cleared_rent(setup, record, 300.0))

    def test_rent_moves_only_a_share_of_the_way_when_demand_changes(self):
        setup, record = economy_with(100.0)
        high = settle(setup, record, 300.0)
        low_cleared = cleared_rent(setup, record, 5.0)        # within the best band: no rent
        self.assertAlmostEqual(low_cleared, 0.0)
        posted = settle(setup, record, 5.0)
        self.assertGreater(posted, low_cleared)
        self.assertLess(posted, high)
        self.assertAlmostEqual(posted, high + land_market.LAND_RENT_ADJUSTMENT_SHARE * (low_cleared - high))

    def test_a_tile_nobody_asks_land_on_decays_instead_of_dropping_to_zero(self):
        setup, record = economy_with(100.0)
        high = settle(setup, record, 300.0)
        land_market.settle_year(setup, record, view(), {})
        self.assertAlmostEqual(record.land_rent["t"], high * (1.0 - land_market.LAND_RENT_ADJUSTMENT_SHARE))

    def test_alternating_demand_swings_rent_less_than_it_swings_what_land_clears_at(self):
        setup, record = economy_with(100.0)
        series = [settle(setup, record, runs) for runs in (300.0, 5.0) * 6]
        late = series[4:]
        cleared = [cleared_rent(setup, record, runs) for runs in (300.0, 5.0)]
        self.assertLess(max(late) - min(late), 0.7 * (max(cleared) - min(cleared)))

    def test_producers_plan_with_and_pay_the_posted_rent(self):
        setup, record = economy_with(100.0)
        settle(setup, record, 300.0)
        before = record.book.balance("producer:t", "coin")
        paid = land_market.settle_year(setup, record, view(), {"producer:t": 5.0})
        self.assertAlmostEqual(record.producers["producer:t"].land_rent_per_run, record.land_rent["t"])
        self.assertAlmostEqual(sum(each.amount for each in paid), before - record.book.balance("producer:t", "coin"))
        self.assertGreater(sum(each.amount for each in paid), 0.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_goods_without_mass.py`

```python
"""Goods whose unit is not a mass must not be carried as 1 kg never-spoiling goods."""
import math
import os
import sys
import unittest

ROOT = os.environ.get("REPO_ROOT", os.getcwd())
sys.path.insert(0, ROOT)

from sim.economy import market_areas, tile_costs  # noqa: E402
from sim.economy.setup import goods_specs  # noqa: E402
from sim.economy.types import TileSpec  # noqa: E402
from sim.world import transport  # noqa: E402

GOODS = ["ox", "mule", "hectare_land", "mechanical_mj", "stone_tons", "stone_blocks", "brick_1000",
         "timber_m3", "wheat_kg"]


def specs():
    return goods_specs({good: "" for good in GOODS}, {})


class GoodsWithoutMass(unittest.TestCase):
    def test_animals_weigh_their_live_weight(self):
        self.assertEqual(specs()["ox"].unit_mass_kg, transport.OX_BODY_MASS_KG)
        self.assertEqual(specs()["mule"].unit_mass_kg, transport.MULE_BODY_MASS_KG)

    def test_ground_and_energy_cannot_be_carried(self):
        for good in ("hectare_land", "mechanical_mj"):
            self.assertFalse(specs()[good].portable, good)
        self.assertTrue(specs()["wheat_kg"].portable)

    def test_tonne_unit_is_a_tonne(self):
        self.assertEqual(specs()["stone_tons"].unit_mass_kg, 1000.0)

    def test_heavy_building_goods_are_not_a_kilogram(self):
        for good in ("stone_blocks", "brick_1000", "timber_m3"):
            self.assertGreater(specs()[good].unit_mass_kg, 100.0, good)

    def test_immobile_good_has_no_market_area_beyond_its_tile(self):
        tiles = {name: TileSpec(name, 40.0, longitude, 1000.0, False, ("a", "b"), 0.5, 1.0)
                 for name, longitude in (("a", 0.0), ("b", 1.0))}
        table = tile_costs.CarriageTable(tiles, tile_costs.build_edges(tiles), {"draught": 1.0, "pack": 1.0}, {})
        spec = specs()["hectare_land"]
        self.assertEqual(market_areas.value_per_tonne(spec, 100.0), 0.0)
        areas = market_areas.partition(tiles, table, market_areas.value_per_tonne(spec, 100.0), {"a": 1, "b": 1})
        self.assertEqual(len(areas), 2)
        self.assertTrue(math.isinf(spec.unit_mass_kg))


if __name__ == "__main__":
    unittest.main()
```

## `test_metal_gap_timing.py`

```python
"""The audit's metal gap is read at a consistent point: coin wear booked at year close, after the mint
last matched its metal to the coin, is not a gap; it is reported as metal awaiting wear."""
import math
import unittest

from sim import economy_validate
from sim.economy import money_audit
from sim.economy.accounts import Book
from sim.economy.metal_stock import yearly_wear
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, CurrencySpec, GoodsMove, Transfer


class Holder:
    def __init__(self, book, currency):
        self.book, self.currency = book, currency


def worn_book(metal):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "alice", "coin", 1000.0, "opening"))
    book.move(GoodsMove(EDGE_PRODUCTION, EDGE_MINT, "silver", "t1", metal, "metal"))
    book.start_year()
    spec = CurrencySpec("coin", "struck_coin", "silver", 0.005, None)
    book.transfer_many(yearly_wear({"alice": 1000.0}, spec))
    return Holder(book, spec)


class SyntheticWear(unittest.TestCase):
    def test_wear_after_reconciliation_is_not_a_gap(self):
        audit = money_audit.year_report(worn_book(5.0))
        self.assertAlmostEqual(audit.metal_gap["coin"], 0.0, places=9)
        self.assertAlmostEqual(audit.metal_awaiting_wear["coin"], 10.0 * 0.005, places=9)

    def test_a_real_excess_still_shows(self):
        self.assertAlmostEqual(money_audit.year_report(worn_book(6.0)).metal_gap["coin"], 1.0, places=9)


class PlayedGames(unittest.TestCase):
    def _gaps(self, civ, years):
        game = economy_validate.new_game(civ, 1)
        out = []
        for _year in range(years):
            game.step()
            record = game.economy.agent.economy().record
            audit = money_audit.year_report(record)
            held = math.fsum(record.book.holdings(EDGE_MINT)["goods"].get(record.currency.backing_good, {}).values())
            out.append((audit.metal_gap[record.currency.currency_id], held))
        return out

    def test_gap_is_zero_each_year(self):
        for civ in ("rome_100ad", "england_1300", "norse_900ad"):
            for gap, held in self._gaps(civ, 2):
                self.assertLess(abs(gap), 1e-6 * held, civ)


if __name__ == "__main__":
    unittest.main()
```

## `test_underflow.py`

```python
"""A balance left a float's underflow below zero (smaller than the smallest normal float) is rounding
residue, not an overdraft; a real overdraft still fails."""
import unittest

from sim.economy.accounts import Book, InsufficientFunds
from sim.economy.types import Transfer


class UnderflowTests(unittest.TestCase):
    def test_a_subnormal_residue_is_not_an_overdraft(self):
        book = Book()
        book.transfer(Transfer("edge:issue", "a", "coin", 1e-320, "seed"))
        book.post([Transfer("a", "b", "coin", 1e-320 + 5e-324, "pay")], [])   # leaves -5e-324

    def test_a_real_overdraft_still_fails(self):
        book = Book()
        book.transfer(Transfer("edge:issue", "a", "coin", 1.0, "seed"))
        with self.assertRaises(InsufficientFunds):
            book.transfer(Transfer("a", "b", "coin", 1.5, "pay"))


if __name__ == "__main__":
    unittest.main()
```

## `test_filled_overpaid_trade.py`

```python
"""A trade whose posts are all filled but whose pay is far over its ask still draws workers."""
import unittest

from sim.economy import labour_asks


class FilledOverpaidTradeTests(unittest.TestCase):
    def test_a_filled_trade_paid_far_over_its_ask_draws_workers(self):
        moved = labour_asks.follow_pay({"labourer": 1000.0, "smith": 0.36}, {"labourer": 1.0, "smith": 2000.0},
                                       {"labourer": 1000.0, "smith": 0.36})
        self.assertGreater(moved["smith"], 0.36)

    def test_a_filled_trade_paid_its_ask_draws_nobody(self):
        workforce = {"labourer": 1000.0, "smith": 0.36}
        self.assertEqual(labour_asks.follow_pay(workforce, {"labourer": 1.0, "smith": 1.0},
                                                {"labourer": 1000.0, "smith": 0.36}), workforce)


if __name__ == "__main__":
    unittest.main()
```

## `test_producer_stock_holding.py`

```python
"""A producer working far below its plant's capacity is short of cash only against the scale it works
at (plus the change one year allows), not against its whole plant, so it is not forced to dump stock at
any price. Its cash target, and so its dividends, are unchanged."""
import unittest

from sim.economy import producers, producers_close
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})
SPECS = {}                                      # no spoilage data: the good keeps


class View:
    year = 3

    def __init__(self, prices, wages, cash, rate=0.05):
        self.prices, self.wages, self.cash_held, self.rate = prices, wages, cash, rate

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return self.cash_held

    def stock(self, agent, good, tile):
        return 0.0


def view(cash):
    return View({"grain": 2.0, "seed": 1.0}, {"hand": 1.0}, cash)     # a run costs 2 + 5 = 7


def small_scale_producer(**changes):
    """Capacity 100 runs, works 4; the whole plant's working capital is 700, the scale it could reach
    next year (4 + a quarter of capacity = 29 runs) needs 203."""
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=100.0,
                last_runs=4.0, expected_sales=4.0, expected_prices={"grain": 2.0}, cash_target=700.0)
    base.update(changes)
    return producers.Producer(**base)


def offered(producer, cash, stock=50.0):
    shortfall = max(0.0, producer.cash_target - cash)
    return producers.offers(producer, FARM, view(cash), {"grain": stock}, shortfall, 0.05, SPECS)[0]


class DistressAgainstWorkingScaleTests(unittest.TestCase):
    def test_stock_is_held_for_a_better_price_when_cash_covers_the_scale_it_can_reach(self):
        self.assertGreater(offered(small_scale_producer(), cash=300.0).reservation_price, 0.0)

    def test_stock_is_still_dumped_when_cash_is_far_short_of_even_that_scale(self):
        self.assertEqual(offered(small_scale_producer(), cash=0.0).reservation_price, 0.0)

    def test_a_partly_short_producer_asks_less_than_a_flush_one(self):
        flush = offered(small_scale_producer(), cash=700.0).reservation_price
        short = offered(small_scale_producer(), cash=190.0).reservation_price
        self.assertGreater(flush, short)
        self.assertGreater(short, 0.0)

    def test_a_producer_with_no_history_is_short_against_its_whole_plant(self):
        new = small_scale_producer(last_runs=-1.0, expected_sales=0.0)
        self.assertEqual(offered(new, cash=300.0).reservation_price, 0.0)

    def test_the_cash_target_and_dividends_still_follow_the_whole_plant(self):
        closed = producers_close.close_year(small_scale_producer(), FARM, 300.0, 100.0, view(1e6)).producer
        whole_plant = producers_close.working_capital_target(FARM, closed.capacity_runs, {"seed": 1.0}, {"hand": 1.0})
        self.assertAlmostEqual(closed.cash_target, whole_plant)


if __name__ == "__main__":
    unittest.main()
```

## `test_input_price_expectations.py`

```python
"""A producer plans against the input prices it expects, not only last year's: a one-year spike in an
input's price does not swing its runs, so a chain of producers does not hand a swing down the chain."""
import unittest

from sim.economy import producers
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages=None, rate=0.05):
        self.prices, self.wages, self.rate = prices, wages or {"hand": 1.0}, rate

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0,
                expected_prices={"grain": 0.9})              # a run earns 9 against 7 at steady prices
    base.update(changes)
    return producers.Producer(**base)


class InputExpectationTests(unittest.TestCase):
    def test_an_input_expectation_moves_part_of_the_way_to_the_latest_price(self):
        producer = farmer(expected_prices={"grain": 0.9, "seed": 1.0})
        updated = producers.next_expectations(producer, FARM, View({"grain": 0.9, "seed": 3.0}))
        share = producers.EXPECTATION_ADJUSTMENT_SHARE
        self.assertAlmostEqual(updated["seed"], 1.0 + share * (3.0 - 1.0))

    def test_an_input_seen_for_the_first_time_is_expected_at_its_latest_price(self):
        updated = producers.next_expectations(farmer(), FARM, View({"grain": 0.9, "seed": 3.0}))
        self.assertAlmostEqual(updated["seed"], 3.0)

    def test_a_one_year_spike_in_an_input_price_cuts_runs_less_when_the_steady_price_is_expected(self):
        spike = View({"grain": 0.9, "seed": 3.0})            # live run cost 6 + 5 = 11 against revenue 9
        forgetful = producers.plan(farmer(), FARM, spike, 1000.0).runs
        remembering = producers.plan(farmer(expected_prices={"grain": 0.9, "seed": 1.0}), FARM, spike, 1000.0).runs
        self.assertGreater(remembering, forgetful + 1.0)

    def test_orders_for_the_input_are_still_priced_at_what_the_market_asks_now(self):
        spike = View({"grain": 0.9, "seed": 3.0})
        plan = producers.plan(farmer(expected_prices={"grain": 0.9, "seed": 1.0}), FARM, spike, 1000.0)
        self.assertGreater(plan.runs, 0.0)
        self.assertAlmostEqual(plan.bids[0].reference_price, 3.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_idle_producer_holds_stock.py`

```python
"""A producer whose runs do not pay needs no working capital, so it is not pressed to dump stock at zero."""
import unittest

from sim.economy import producers
from sim.economy.types import Recipe

SMELT = Recipe("smelt", {"metal": 10.0}, {"ore": 4.0}, {"smith": 1.0})


class View:
    year = 3

    def __init__(self, prices, wages=None):
        self.prices, self.wages = prices, wages if wages is not None else {"smith": 1.0}

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return 0.0


def smelter(**changes):
    base = dict(agent_id="s1", owner="lord", recipe_id="smelt", tile="t", capacity_runs=10.0, last_runs=10.0,
                expected_sales=10.0, cash_target=200.0, expected_prices={"metal": 1.0, "ore": 1.0})
    base.update(changes)
    return producers.Producer(**base)


def reservation(view, shortfall=150.0, **changes):
    rows = producers.offers(smelter(**changes), SMELT, view, {"metal": 5.0}, shortfall, 0.05, {})
    return rows[0].reservation_price


class IdleProducerTests(unittest.TestCase):
    def test_a_run_that_does_not_pay_leaves_the_stock_at_its_holding_reservation(self):
        # revenue per run 10 at the expected price; the ore alone costs 400 a run at the market
        dear_ore = View({"metal": 1.0, "ore": 100.0}, {"smith": 1.0})
        held = reservation(dear_ore, expected_prices={"metal": 1.0, "ore": 100.0})
        self.assertAlmostEqual(held, 1.0 / 1.05)

    def test_a_run_that_pays_still_presses_a_cash_short_producer(self):
        cheap_ore = View({"metal": 1.0, "ore": 0.01}, {"smith": 0.1})
        pressed = reservation(cheap_ore, shortfall=150.0, expected_prices={"metal": 1.0, "ore": 0.01})
        self.assertLess(pressed, 1.0 / 1.05)

    def test_a_run_that_cannot_be_priced_does_not_press_the_producer(self):
        no_wage = View({"metal": 1.0, "ore": 0.01}, {})
        self.assertAlmostEqual(reservation(no_wage, expected_prices={"metal": 1.0, "ore": 0.01}), 1.0 / 1.05)


if __name__ == "__main__":
    unittest.main()
```

## `test_economy_entrant_sizing.py`

```python
"""A newcomer is built to the trade it can see and the supply its plant and inputs can get, not to the whole
gap buyers left. Copy to sim/tests/ (it imports the View helper from test_economy_producers)."""
import unittest

from sim.economy import entry, entry_sizing
from sim.economy.types import Recipe
from sim.tests.test_economy_producers import View

SALT = Recipe("boil_salt", {"salt": 10.0}, {"firewood": 5.0}, {"hand": 2.0}, {"pan": 1.0}, {}, 10.0)


def market(unmet):
    return {("salt", "area"): entry.UnmetDemand("salt", "area", "anchor", unmet)}


def view():
    return View(prices={"salt": 1.0, "firewood": 0.1, "pan": 2.0}, wages={"hand": 0.2})


def plans(unmet, volumes):
    """volumes: good -> traded last year; a good left out has no market."""
    return entry.entry_plans({"boil_salt": SALT}, view(), market(unmet), None, None,
                             lambda good, tile: volumes.get(good))


class EntrantSizingTests(unittest.TestCase):
    def test_a_gap_far_beyond_the_trade_is_sized_to_the_trade(self):
        # buyers wanted 1e6 more salt, but only 200 was traded: the works is built for a share of the 200
        chosen = plans(1e6, {"salt": 200.0, "firewood": 1e9, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_TRADED_VOLUME * 200.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_a_gap_inside_the_trade_keeps_its_share(self):
        chosen = plans(100.0, {"salt": 1e6, "firewood": 1e9, "pan": 1e9})
        self.assertAlmostEqual(chosen[0].runs, 100.0 * entry.ENTRY_SHARE_OF_UNMET_DEMAND / SALT.outputs["salt"])

    def test_scarce_plant_goods_set_the_size_that_is_built(self):
        # only 3 pans traded: the plant, and so the loan, is for what can be bought, not for the whole plan
        chosen = plans(1e6, {"salt": 1e9, "firewood": 1e9, "pan": 3.0})
        expected = entry_sizing.ENTRY_SHARE_OF_INPUT_VOLUME * 3.0 / SALT.plant_goods["pan"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_scarce_inputs_set_the_size(self):
        chosen = plans(1e6, {"salt": 1e9, "firewood": 20.0, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_INPUT_VOLUME * 20.0 / SALT.inputs["firewood"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_a_market_that_traded_nothing_gets_a_trial_size_not_the_gap(self):
        chosen = plans(1000.0, {"salt": 0.0, "firewood": 1e9, "pan": 1e9})
        expected = entry_sizing.ENTRY_SHARE_OF_UNTRADED_DEMAND * 1000.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_untraded_inputs_give_the_trial_size_too(self):
        chosen = plans(1000.0, {"salt": 1e9, "firewood": 0.0, "pan": 0.0})
        expected = entry_sizing.ENTRY_SHARE_OF_UNTRADED_DEMAND * 1000.0 / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected)

    def test_goods_with_no_market_do_not_limit(self):
        chosen = plans(100.0, {"salt": 1e6})
        self.assertAlmostEqual(chosen[0].runs, 100.0 * entry.ENTRY_SHARE_OF_UNMET_DEMAND / SALT.outputs["salt"])


if __name__ == "__main__":
    unittest.main()
```

## `test_producer_stale_ask.py`

```python
"""A seller left holding goods nobody bought at its ask lowers the ask and what it expects to get, and does
not stop planning runs for good because the sales it recorded were at an ask above every bid."""
import math
import unittest

from sim.economy import producers
from sim.economy.types import GoodSpec, Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages, stock=0.0, rate=0.05):
        self.prices, self.wages, self.held, self.rate = prices, wages, stock, rate

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 1000.0

    def stock(self, agent, good, tile):
        return self.held if good == "grain" else 0.0


def seller(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0,
                last_runs=1.0, expected_sales=1.0, expected_prices={"grain": 0.7})
    base.update(changes)
    return producers.Producer(**base)


def frozen_market(stock):
    """The market remembers the price the seller already expects: nothing cleared, nothing moved it."""
    return View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock)


class UnsoldAskTests(unittest.TestCase):
    def test_unsold_stock_lowers_the_expected_price(self):
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=500.0))["grain"]
        self.assertLess(expected, 0.63)

    def test_no_stock_left_keeps_the_expectation(self):
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=0.0))["grain"]
        self.assertGreater(expected, 0.65)

    def test_the_reservation_follows_the_expectation_down_year_after_year(self):
        producer = seller()
        view = frozen_market(stock=500.0)
        reservations = []
        for _year in range(8):
            producer = producers.replace(producer, expected_prices=producers.next_expectations(producer, FARM, view))
            offer, = producers.offers(producer, FARM, view, {"grain": 500.0}, 0.0, 0.05, {"grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food")})
            reservations.append(offer.reservation_price)
        self.assertTrue(all(later < earlier for earlier, later in zip(reservations, reservations[1:])))
        self.assertLess(reservations[-1], 0.2 * reservations[0])

    def test_sales_recorded_at_too_high_an_ask_do_not_stop_runs_for_good(self):
        producer = seller(expected_sales=1e-6)
        held_in_runs = 0.1
        runs = producers.runs_for_stock(producer, FARM, View({}, {}, stock=held_in_runs * FARM.outputs["grain"]))
        self.assertGreater(runs, 0.0)
        self.assertTrue(math.isfinite(runs))

    def test_a_large_unsold_stock_still_holds_runs_back(self):
        producer = seller(expected_sales=1e-6)
        runs = producers.runs_for_stock(producer, FARM, View({}, {}, stock=50.0 * FARM.outputs["grain"]))
        self.assertEqual(runs, 0.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_frozen_markets.py`

```python
"""A market with offers and no bids drifts toward the lowest ask instead of freezing, and the first trade
after such quiet years moves the remembered price only part of the way."""
import unittest

from sim.economy import market_memory_asks as asks
from sim.economy.market_memory import MarketMemory
from sim.economy.types import Bid, Offer


def offer(ask):
    return Offer("seller", "limestone_kg", "area", "tile", 1.0, ask)


def bid(budget=10.0):
    return Bid("buyer", "limestone_kg", "area", "tile", 1.0, 0.0, 1.0, 0.0, budget)


class NoBidMemoryTests(unittest.TestCase):
    def test_remembered_price_moves_part_of_the_way_to_the_lowest_ask(self):
        price = asks.price_after_no_bids(1000.0, [], [offer(500.0), offer(100.0)])
        self.assertLess(price, 1000.0)
        self.assertGreater(price, 100.0)

    def test_repeated_years_converge_on_the_ask(self):
        price = 1000.0
        for _year in range(30):
            price = asks.price_after_no_bids(price, [], [offer(100.0)]) or price
        self.assertLess(price, 101.0)

    def test_an_ask_above_the_memory_does_not_raise_it(self):
        self.assertIsNone(asks.price_after_no_bids(100.0, [], [offer(900.0)]))

    def test_a_market_with_a_live_bid_is_left_to_the_other_rules(self):
        self.assertIsNone(asks.price_after_no_bids(1000.0, [bid()], [offer(100.0)]))

    def test_a_broke_buyer_is_no_bid(self):
        self.assertIsNotNone(asks.price_after_no_bids(1000.0, [bid(budget=0.0)], [offer(100.0)]))

    def test_nothing_remembered_or_nothing_offered_gives_none(self):
        self.assertIsNone(asks.price_after_no_bids(None, [], [offer(100.0)]))
        self.assertIsNone(asks.price_after_no_bids(1000.0, [], []))


class ResumedTradeTests(unittest.TestCase):
    def test_years_without_bids_are_counted_and_reset(self):
        memory = MarketMemory()
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 1)
        self.assertEqual(asks.note_bids(memory, "k", [bid()], [offer(1.0)]), 2)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)

    def test_first_trade_after_quiet_years_moves_part_of_the_way(self):
        price = asks.price_after_resumed_trade(10.0, 1000.0, 3)
        self.assertGreater(price, 10.0)
        self.assertLess(price, 1000.0)

    def test_a_market_that_was_bid_in_adopts_the_volume_rule_price(self):
        self.assertEqual(asks.price_after_resumed_trade(10.0, 1000.0, 0), 1000.0)

    def test_the_count_is_saved_with_the_memory(self):
        self.assertIn("years_without_bids", MarketMemory().__dict__)


if __name__ == "__main__":
    unittest.main()
```

## `test_input_ceiling.py`

```python
"""A producer never offers more for an input than the run is worth at the input prices it now sees.

Run: python3 -m unittest discover -s <this directory>   (from the repository root)
"""
import unittest

from sim.economy import producers
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages):
        self.prices, self.wages = prices, wages

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0)
    base.update(changes)
    return producers.Producer(**base)


class InputCeilingTests(unittest.TestCase):
    def test_a_run_that_no_longer_pays_at_the_live_input_price_bids_no_more_than_that_price(self):
        # the producer still expects seed at 1 and grain at 2 (a run earns 20 against 7), but seed now sells at 10,
        # where a run costs 25 and earns 20: it has no margin to offer for seed
        who = farmer(expected_prices={"grain": 2.0, "seed": 1.0})
        plan = producers.plan(who, FARM, View({"grain": 2.0, "seed": 10.0}, {"hand": 1.0}), 1e6)
        self.assertGreater(plan.runs, 0.0)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        self.assertLessEqual(seed.maximum_price, 10.0 + 1e-9)

    def test_a_run_that_pays_at_the_live_input_price_bids_up_to_the_price_that_breaks_even(self):
        who = farmer(expected_prices={"grain": 2.0, "seed": 1.0})
        plan = producers.plan(who, FARM, View({"grain": 2.0, "seed": 1.0}, {"hand": 1.0}), 1e6)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        self.assertGreater(seed.maximum_price, 1.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_merchant_shares.py`

```python
"""Merchants chasing one destination share it: across its sources one merchant's bids add up to its
share of what the destination usually trades, and rivals together to the group's share.

Run: python3 -m unittest discover -s <this directory> -t /home/user/bootstrap-history/.claude/worktrees/agent-a5160b1c849cb3a25
(or put the repository root on PYTHONPATH and run `python3 -m unittest test_merchant_shares`).
"""
import unittest

from sim.economy import merchants, merchants_credit
from sim.economy.market_areas import AreaMap
from sim.economy.merchants import Merchant
from sim.economy.tile_costs import CarriageTable, Edge
from sim.economy.types import GoodSpec

TILES = ("a", "b", "c", "d")        # a, b, c are cheap sources; d is the dear destination
SALT = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
SPECS = {"salt": SALT}
DESTINATION_VOLUME = 100.0


class View:
    year = 1

    def price(self, good, area):
        return None

    def interest_rate(self, currency):
        return 0.0


def world():
    edges = [Edge(tile, "d", ("land",), 100.0) for tile in "abc"]
    carriage = CarriageTable(TILES, edges, {"land": 0.01})
    area_map = AreaMap(TILES, carriage, [(SALT, 2.0)], {"a": 10.0, "b": 9.0, "c": 8.0, "d": 5.0}, threshold_share=0.01)
    return carriage, area_map


def merchant(name="m1"):
    carriage, area_map = world()
    area = {tile: area_map.area_of("salt", tile) for tile in TILES}
    expected = {("salt", area["a"]): 2.0, ("salt", area["b"]): 2.0, ("salt", area["c"]): 2.0, ("salt", area["d"]): 5.0}
    return Merchant(name, "a", "owner", 100.0, expected, {("salt", area["d"]): DESTINATION_VOLUME})


def total_bid(orders):
    return sum(bid.flexible_quantity for bid in orders.bids)


class OneMerchantAcrossSourcesTests(unittest.TestCase):
    def test_bids_from_every_source_together_stay_within_the_destinations_share(self):
        carriage, area_map = world()
        orders = merchants.orders(merchant(), View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertLessEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME + 1e-9)

    def test_the_whole_share_is_still_bid_when_cash_allows(self):
        carriage, area_map = world()
        orders = merchants.orders(merchant(), View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertAlmostEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)

    def test_a_loan_request_does_not_count_the_same_room_once_per_source(self):
        carriage, area_map = world()
        who = merchant()
        who.capital_base = 1e6          # the leverage limit is not what binds
        asked = merchants_credit.credit_request(who, View(), carriage, area_map, 0.0, {}, SPECS, 0.0, 0.0, "coin")
        self.assertIsNotNone(asked)
        # the cargo fits the one destination: its share of the volume, at no more than price plus carriage a unit
        self.assertLessEqual(asked.amount, merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME * (2.0 + 1.0) + 1e-9)


class SourceTests(unittest.TestCase):
    def test_a_merchant_does_not_bid_for_more_than_the_source_usually_sells(self):
        carriage, area_map = world()
        who = merchant()
        source = area_map.area_of("salt", "a")
        who.expected_volumes[("salt", source)] = 2.0     # the area sold two units last year; the destination takes thirty
        orders = merchants.orders(who, View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        from_source = sum(bid.flexible_quantity for bid in orders.bids if bid.area == source)
        self.assertLessEqual(from_source, 2.0 + 1e-9)

    def test_the_destinations_room_goes_to_sources_that_can_fill_it(self):
        carriage, area_map = world()
        who = merchant()
        who.expected_volumes[("salt", area_map.area_of("salt", "a"))] = 2.0        # the best-priced source has little to sell
        who.expected_volumes[("salt", area_map.area_of("salt", "b"))] = 1000.0
        who.expected_volumes[("salt", area_map.area_of("salt", "c"))] = 1000.0
        orders = merchants.orders(who, View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertAlmostEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)
        self.assertGreater(len({bid.area for bid in orders.bids}), 1)


class RivalMerchantsTests(unittest.TestCase):
    def test_merchants_together_stay_within_the_groups_share(self):
        carriage, area_map = world()
        shares = merchants.RouteShares()
        placed = 0.0
        for name in ("m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9"):
            placed += total_bid(merchants.orders(merchant(name), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        from sim.economy import merchants_shares
        self.assertLessEqual(placed, merchants_shares.MERCHANT_GROUP_SHARE * DESTINATION_VOLUME + 1e-9)

    def test_a_late_merchant_gets_what_the_earlier_ones_left(self):
        carriage, area_map = world()
        shares = merchants.RouteShares()
        first = total_bid(merchants.orders(merchant("m1"), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        second = total_bid(merchants.orders(merchant("m2"), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        self.assertAlmostEqual(first, merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)
        self.assertGreater(second, 0.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_resumed_trade_memory.py`

```python
"""A sliver of trade after years with buyers and no seller must not reset the remembered price.
Run from the repo root: python3 <this file>"""
import sys
import types
import unittest

sys.path.insert(0, ".")
from sim.economy import year_goods
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory, market_key
from sim.economy.types import EDGE_ISSUE, EDGE_PRODUCTION, Bid, GoodsMove, Offer, Transfer
from sim.economy.year_ledger import YearLedger

CURRENCY = "coin"
KEY = market_key("brass", "area")


def one_year(memory, book, bids, offers):
    setup = types.SimpleNamespace(recipes={}, tax_forms=[], currency_id=CURRENCY, opening_prices={"brass": 4.0},
                                  specs={}, state_agent="state")
    record = types.SimpleNamespace(producers={}, memory=memory, book=book, volumes={})
    order_book = {("brass", "area"): (list(bids), list(offers))}
    year_goods.clear_goods(setup, record, None, None, order_book, {}, YearLedger())


def household_bid():
    # flexible demand for a good bought for variety: no ceiling, budget-limited
    return Bid("household", "brass", "area", "tile", 0.0, 1000.0, 4.0, 2.0, 4000.0, 1)


def funded_book(quantity):
    book = Book()
    book.transfer(Transfer(EDGE_ISSUE, "household", CURRENCY, 1e9, "seed"))
    if quantity > 0.0:
        book.move(GoodsMove(EDGE_PRODUCTION, "smith", "brass", "tile", quantity, "seed"))
    return book


class ResumedAfterDryYears(unittest.TestCase):
    def memory(self, dry_years):
        memory = MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0})
        for _year in range(dry_years):          # buyers and no seller, as the game plays it
            one_year(memory, funded_book(0.0), [household_bid()], [])
        return memory

    def test_sliver_of_trade_after_dry_years_cannot_reset_the_memory(self):
        memory = self.memory(30)
        sliver = Offer("smith", "brass", "area", "tile", 0.11, 0.1)
        one_year(memory, funded_book(0.11), [household_bid()], [sliver])
        self.assertLess(memory.prices[KEY], 4.0 * 6.0)

    def test_real_supply_after_dry_years_still_brings_the_memory_to_the_market_price(self):
        def full_years(memory):
            for _year in range(8):
                one_year(memory, funded_book(500.0), [household_bid()], [Offer("smith", "brass", "area", "tile", 500.0, 0.1)])
            return memory.prices[KEY]
        ordinary = full_years(MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0}))
        after_dry = full_years(self.memory(3))
        self.assertAlmostEqual(after_dry / ordinary, 1.0, delta=0.05)

    def test_sliver_in_a_market_that_never_cleared_cannot_move_the_opening_estimate_far(self):
        memory = MarketMemory(prices={KEY: 4.0})        # opening estimate: no usual volume, never cleared
        sliver = Offer("smith", "brass", "area", "tile", 0.11, 0.1)
        one_year(memory, funded_book(0.11), [household_bid()], [sliver])
        self.assertLess(memory.prices[KEY], 4.0 * 6.0)

    def test_ordinary_market_still_follows_its_price(self):
        memory = MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0})
        one_year(memory, funded_book(500.0), [household_bid()], [Offer("smith", "brass", "area", "tile", 500.0, 0.1)])
        self.assertNotEqual(memory.prices[KEY], 4.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_household_ceilings.py`

```python
"""A cohort's bid for a good is capped at what one household of its class can pay for one unit."""
import dataclasses
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())
from sim.economy import households  # noqa: E402
from sim.economy.types import GoodSpec  # noqa: E402
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD  # noqa: E402

NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
        "adornment": {"surplus_budget_share": 0.5},
    },
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "beads": {"satisfies": {"adornment": 1.0}},
        "gold_leaf": {"satisfies": {"adornment": 1.0}},
    },
}
SPECS = {name: GoodSpec(name, 1.0, 0.0, 0.0, name) for name in ("grain", "beads", "gold_leaf")}
BASKET = households.make_basket(NEED_DATA, {})


class View:
    year = 1

    def __init__(self, prices):
        self.prices = prices

    def price(self, good, area):
        return self.prices.get(good)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return 0.0


def orders_for(income_per_person, people=100000.0, gold_price=500.0):
    income = income_per_person * people
    cohort = dataclasses.replace(households.Cohort("household:t:0", "t", 0, people, people / 2, 0.3),
                                 last_year_spending=income)
    view = View({"grain": 1.0, "beads": 2.0, "gold_leaf": gold_price})
    return households.goods_orders(cohort, view, income, income, BASKET, SPECS), people


def bid_for(orders, good):
    return next((bid for bid in orders.bids if bid.good == good), None)


class HouseholdCeilingTests(unittest.TestCase):
    def test_a_poor_tier_has_no_bid_for_a_good_dearer_than_its_household_can_pay(self):
        orders, _people = orders_for(income_per_person=260.0)
        self.assertIsNone(bid_for(orders, "gold_leaf"))
        self.assertIsNotNone(bid_for(orders, "beads"))        # its adornment money goes to the cheap good

    def test_a_rich_tier_can_bid_for_the_dear_good(self):
        orders, _people = orders_for(income_per_person=200000.0)
        self.assertIsNotNone(bid_for(orders, "gold_leaf"))

    def test_no_bid_asks_more_than_one_household_earns(self):
        for income_per_person in (260.0, 2000.0, 200000.0):
            orders, _people = orders_for(income_per_person=income_per_person)
            for bid in orders.bids:
                self.assertLessEqual(bid.maximum_price, income_per_person * PERSONS_PER_HOUSEHOLD, bid.good)

    def test_a_dearer_tier_can_pay_more_per_unit(self):
        poor, _people = orders_for(income_per_person=2000.0, gold_price=50.0)
        rich, _people = orders_for(income_per_person=200000.0, gold_price=50.0)
        self.assertLess(bid_for(poor, "gold_leaf").maximum_price, bid_for(rich, "gold_leaf").maximum_price)

    def test_floor_goods_are_never_dropped(self):
        orders, _people = orders_for(income_per_person=150.0)    # cannot cover its food floor
        self.assertIsNotNone(bid_for(orders, "grain"))
        self.assertGreater(bid_for(orders, "grain").floor_quantity, 0.0)


if __name__ == "__main__":
    unittest.main()
```

## `test_areas_cache.py`

```python
"""Run with: python3 <this file>."""
import dataclasses
import sys
import unittest

sys.path.insert(0, "/home/user/bootstrap-history/.claude/worktrees/agent-ac1af985b152b0665")
from sim.tests.test_economy_market_areas import AreaMapTests as Fixture


class AreasCacheTests(Fixture):
    def test_repeated_calls_return_the_same_areas(self):
        area_map = self.build()
        first = area_map.areas("grain_kg")
        self.assertIs(area_map.areas("grain_kg"), first)

    def test_areas_name_their_good_and_goods_do_not_mix(self):
        area_map = self.build()
        for good in ("grain_kg", "silver_kg"):
            self.assertTrue(all(area.good_id == good for area in area_map.areas(good)))

    def test_cached_areas_equal_a_fresh_replacement(self):
        area_map = self.build()
        for good in area_map.goods():
            partition = area_map._partitions[area_map._bucket_of_good[good]]
            fresh = tuple(dataclasses.replace(area, good_id=good) for area in partition)
            self.assertEqual(area_map.areas(good), fresh)


if __name__ == "__main__":
    unittest.main(argv=["x", "AreasCacheTests.test_repeated_calls_return_the_same_areas",
                        "AreasCacheTests.test_areas_name_their_good_and_goods_do_not_mix",
                        "AreasCacheTests.test_cached_areas_equal_a_fresh_replacement"])
```

## `test_speed2.py`

```python
import math
import sys
sys.path.insert(0, "/home/user/bootstrap-history/.claude/worktrees/agent-a0ec4c041385ebe2e")
from sim.economy.accounts import Book, InsufficientFunds
from sim.economy.households_basket import price_ceilings
from sim.economy.types import Transfer


def old_ceilings(shares):
    cost_per_unit = sorted((price / effect, good) for good, price, effect, _share in shares)
    result = []
    for good, price, effect, _share in shares:
        others = [cost for cost, other in cost_per_unit if other != good]
        parity = others[0] * effect if others else math.inf
        result.append(parity if parity >= price else math.inf)
    return tuple(result)


def test_ceilings_match_sorted_form():
    shares = [("a", 2.0, 1.0, 0.5), ("b", 3.0, 2.0, 0.3), ("c", 9.0, 1.0, 0.2)]
    assert price_ceilings(shares) == old_ceilings(shares)
    assert price_ceilings(shares[:1]) == (math.inf,)


def test_batch_overdraft_names_the_first_payer_in_order():
    book = Book()
    book.transfer(Transfer("edge:issue", "z", "coin", 5.0, "seed"))
    book.transfer(Transfer("edge:issue", "a", "coin", 5.0, "seed"))
    try:
        book.post([Transfer("z", "m", "coin", 9.0, "x"), Transfer("a", "m", "coin", 9.0, "x")], [])
    except InsufficientFunds as error:
        assert str(error).startswith("a would hold")
    else:
        raise AssertionError("no overdraft raised")
    assert book.balance("a", "coin") == 5.0


if __name__ == "__main__":
    test_ceilings_match_sorted_form()
    test_batch_overdraft_names_the_first_payer_in_order()
    print("ok")
```

## `test_record_plain.py`

```python
import dataclasses
import json
import sys
import unittest

sys.path.insert(0, "/home/user/bootstrap-history/.claude/worktrees/agent-a8ae1105e17ccbe19")

from sim.economy.record_plain import plain
from sim.economy.producers import Producer
from sim.economy.market_memory import MarketMemory


class PlainTest(unittest.TestCase):
    def test_matches_asdict_and_shares_nothing(self):
        producer = Producer("p", "o", "r", "t", 2.0, expected_prices={"wheat_kg": 1.5})
        memory = MarketMemory(year=3, prices={"wheat_kg|a": 2.0}, trade_age={"wheat_kg|a": 1})
        for item in (producer, memory):
            self.assertEqual(plain(item), dataclasses.asdict(item))
        copy = plain(producer)
        copy["expected_prices"]["wheat_kg"] = 9.0
        self.assertEqual(producer.expected_prices["wheat_kg"], 1.5)

    def test_tuples_and_lists(self):
        value = {"a": [1, (2, {"b": 3.0})], "c": None}
        self.assertEqual(json.dumps(plain(value)), json.dumps(value))


if __name__ == "__main__":
    unittest.main()
```

## `test_routes_equal.py`

```python
"""New _candidate_routes equals the old one, row for row, over several years of a game and several rates."""
import importlib.util
import os
import sys

sys.path.insert(0, os.getcwd())
from sim import economy_validate as ev
from sim.economy import merchants, year_goods

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sim.economy.merchants_old", os.path.join(here, "merchants_old.py"))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

checked = 0


def compare(merchant, view, carriage, area_map, held, specs, rate):
    global checked
    for each_rate in (rate, 0.0, 0.2):
        assert old._candidate_routes(merchant, view, carriage, area_map, held, specs, each_rate) == \
            merchants._candidate_routes(merchant, view, carriage, area_map, held, specs, each_rate)
        checked += 1


real = merchants.orders


def spy(merchant, view, carriage, area_map, cash, held, specs, rate):
    compare(merchant, view, carriage, area_map, held, specs, rate)
    return real(merchant, view, carriage, area_map, cash, held, specs, rate)


year_goods.merchants.orders = spy
game = ev.new_game("england_1300", 1)
for _ in range(6):
    game.step()
assert checked > 0
print("ok", checked)
```
