"""Complaint 624: a debasement reaches domestic prices through the money supply. A state that recoins at a lighter
weight puts more coin into the economy; the price level it clears at rises against a twin economy that did not
debase. No price is set: the only difference between the two economies is the cut the state decides on each year
(`Economy.strike_lighter_coin`, which `economy_port_year._strike_state_coin` calls with the cut the state's fiscal
response chose, Complaint 625). Built on the engine-free fixture; the whole-game scenario is
test_state_debasement_prices_scenario."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

YEARS = 4
CUT = 0.5   # of the metal in the coin struck again, each year: far past what a state does, so the effect stands clear of noise


def run(cut):
    """The fixture economy over some quiet years, its issuer recoining at `cut` before each year."""
    setup = fixture.small_setup()
    economy = Economy(setup)
    outcomes = []
    for _year in range(YEARS):
        economy.strike_lighter_coin(cut, COIN_RESTRIKE_SHARE_PER_YEAR)
        outcomes.append(economy.step(fixture.quiet_year(setup)))
    return economy, outcomes


def mean_price_level(outcomes):
    return sum(outcome.basket_price_level for outcome in outcomes) / len(outcomes)


class DebasementTests(unittest.TestCase):
    def test_a_cut_puts_more_coin_in_circulation_each_holding_less_metal(self):
        twin, _twin_outcomes = run(0.0)
        debased, _outcomes = run(CUT)
        coin = twin.record.currency.currency_id
        self.assertGreater(debased.record.book.money_supply(coin), 1.05 * twin.record.book.money_supply(coin))
        self.assertLess(debased.record.currency.backing_per_unit, twin.record.currency.backing_per_unit)

    def test_no_cut_leaves_the_coin_whole(self):
        twin, _outcomes = run(0.0)
        self.assertEqual(twin.record.currency.backing_per_unit, fixture.small_setup().currency.backing_per_unit)

    def test_the_price_level_rises_against_the_twin(self):
        _twin, twin_outcomes = run(0.0)
        _debased, outcomes = run(CUT)
        self.assertGreater(mean_price_level(outcomes), 1.05 * mean_price_level(twin_outcomes))


if __name__ == "__main__":
    unittest.main()
