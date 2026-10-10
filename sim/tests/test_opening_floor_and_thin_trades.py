"""On a real default game (agent economy on) the household wage floor stays near the food floor and no trade
quotes above what training a substitute costs (Complaint 434). Builds a game, so it is a slow topic."""
import statistics
import unittest

from .harness import *  # noqa: F401,F403
from sim.economy import households_basket
from sim.world.need_basket import subsistence_cost_per_person
import sim.economy.api as economy_api
from sim.labour import wages

FLOOR_OVER_FOOD_FLOOR = 8.0      # a small multiple: clothing, shelter, fuel, water and vessels together cost a few foods
SUBSTITUTE_SLACK = 1.5           # room for the one-year lag of the unskilled wage the ceiling reads
MASON_SHARE_OF_WORKERS = 0.03       # the opening had a tenth
GOOD_PRICE_DRIFT = 20.0          # times the good's price against wheat at the opening


def _game():
    game = sim(civ="rome_100ad")
    economy = game.economy.agent._economy
    return game, economy, economy.setup, economy.record, economy.view()


class OpeningFloorTests(unittest.TestCase):

    def test_the_household_floors_cost_a_small_multiple_of_the_food_floor(self):
        _game_, _economy, setup, record, view = _game()
        tiles = sorted({cohort.tile for cohort in record.cohorts.values()})
        ratios = []
        for tile in tiles:
            priced = households_basket.need_prices(setup.basket_for(tile), view, tile)
            food = [need for need in priced if need.spec.need_id == "food"]
            if food:
                ratios.append(subsistence_cost_per_person(priced) / subsistence_cost_per_person(food))
        self.assertLessEqual(statistics.median(ratios), FLOOR_OVER_FOOD_FLOOR)

    def test_no_trade_pays_much_above_the_trained_substitute_of_the_unskilled_wage(self):
        # Each area clears against last year's unskilled wage, so a year's lag shows; the people-weighted
        # mean of a trade's wage over its unskilled wage must still sit near its training premium.
        _game_, _economy, setup, record, _view = _game()
        state = record.workforce
        for trade, spec in setup.trades.items():
            if trade == setup.unskilled_trade:
                continue
            weighted = people = 0.0
            for area, by_trade in state.wages.items():
                unskilled = by_trade.get(setup.unskilled_trade)
                held = sum(state.workers.get(area, {}).get(trade, []))
                if unskilled and trade in by_trade and held > 0.0:
                    weighted += held * by_trade[trade] / unskilled
                    people += held
            if people > 0.0:
                premium = wages.training_premium(spec.training_years, setup.opening_rate)
                self.assertLessEqual(weighted / people, premium * SUBSTITUTE_SLACK, trade)

    def test_goods_the_new_needs_call_for_are_not_priced_off_runaway_wages(self):
        # Market prices against wheat's, as at the opening: a thin trade's wage must not drag its good away.
        _game_, _economy, setup, record, _view = _game()

        def median_price(good):
            found = [price for key, price in record.memory.prices.items() if key.split("|")[0] == good]
            return statistics.median(found) if found else None
        wheat_now, wheat_then = median_price("wheat_kg"), setup.opening_prices["wheat_kg"]
        for good in ("ceramic_kg", "ink_kg", "papyrus_sheet"):
            now, then = median_price(good), setup.opening_prices.get(good)
            if now and then:
                self.assertLess((now / wheat_now) / (then / wheat_then), GOOD_PRICE_DRIFT, good)


class OpeningStaffingTests(unittest.TestCase):

    def test_the_opening_does_not_staff_a_building_boom(self):
        # Households open holding the durables they keep in use, so the first year buys replacement, not
        # thirty years of walls: masons stay a small share of working people (they were a tenth).
        from sim.economy import labour_state, opening
        _game_, _economy, setup, _record, _view = _game()
        record, _areas, _carriage = opening.open_economy(setup)
        people = labour_state.people_by_trade_everywhere(record.workforce)
        self.assertLess(people.get("mason", 0.0) / sum(people.values()), MASON_SHARE_OF_WORKERS)


if __name__ == "__main__":
    unittest.main()
