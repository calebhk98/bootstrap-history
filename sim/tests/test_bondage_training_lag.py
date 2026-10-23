"""Complaint 640: people bought arrive untrained: `buy_slaves` queues them in the household's training rows for the training lag
and adds no artisan capacity that day, and `manumit` raises the capacity of trained people only (the untrained rise when they
mature). Each method is called on a stand-in `self` carrying a household written out here."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.labour import labour_bondage
from sim.labour.labour_bondage import BondageMixin

YEAR = 100
PRICE = 250.0


class Bondage(BondageMixin):
    """The household, holdings and money that buying and freeing people touch."""

    def __init__(self, cash=1000.0, room=100.0, employees=None):
        self.cash, self.room, self.paid = cash, room, []
        self.staff = employees or {}
        self.household = types.SimpleNamespace(slaves=0, freedmen=0, manumitted_total=0, artisans=0.0, scholars=0.0, training=[],
                                               reputation=0.0)
        self.holdings = types.SimpleNamespace(market_pressure=0.0)
        self._world = types.SimpleNamespace(
            state=types.SimpleNamespace(household=self.household, holdings=self.holdings, scenario=types.SimpleNamespace(year=YEAR)),
            household=self.household, can_pay=lambda price: price <= self.cash, EDGE_SLAVE_TRADERS="slave_traders",
            pay_edge=lambda edge, price, text: self.paid.append(price),
            refusal_text=lambda what, price: "cannot afford %s" % what)

    def household_room(self):
        return self.room

    def employed_by_trade(self):
        return self.staff

    def employed(self, trade):
        return self.employed_by_trade().get(trade, 0.0)

    def is_craft_trade(self, trade):
        return trade != "scholar"

    def slave_quote(self, people):
        return PRICE

    def _staff_advice(self, kind):
        return "advice"


class BuySlaves(unittest.TestCase):
    def test_the_people_bought_queue_for_the_training_lag_at_the_untrained_worth(self):
        game = Bondage()
        self.assertEqual(game.buy_slaves(12), 12)
        self.assertEqual(game.household.training, [[12 * game.WORKER_EQUIVALENT_UNTRAINED, YEAR + game.TRAINING_YEARS]])

    def test_the_people_bought_add_no_artisan_capacity_the_day_they_arrive(self):
        game = Bondage()
        game.buy_slaves(12)
        self.assertEqual(game.household.artisans, 0.0)

    def test_the_price_is_paid_and_the_slaves_and_the_markets_pressure_are_counted(self):
        game = Bondage()
        game.buy_slaves(12)
        self.assertEqual((game.paid, game.household.slaves, game.holdings.market_pressure), ([PRICE], 12, 12))

    def test_a_purchase_the_purse_cannot_cover_buys_nobody_and_queues_nobody(self):
        game = Bondage(cash=PRICE - 1.0)
        self.assertEqual(game.buy_slaves(12), 0)
        self.assertEqual((game.household.slaves, game.household.training, game.paid), (0, [], []))

    def test_a_purchase_beyond_the_households_room_buys_nobody(self):
        game = Bondage(room=5.0)
        self.assertEqual(game.buy_slaves(12), 0)
        self.assertEqual((game.household.slaves, game.household.training, game.paid), (0, [], []))


class Manumit(unittest.TestCase):
    def freed(self, trained=True, count=4):
        game = Bondage()
        game.household.slaves = count
        if not trained:
            game.household.training = [[count * game.WORKER_EQUIVALENT_UNTRAINED, YEAR + 3.0]]
        return game, game.manumit(count)

    def test_freeing_trained_people_raises_their_capacity_by_the_uplift_not_another_worker(self):
        game, freed = self.freed(trained=True)
        self.assertEqual(freed, 4)
        self.assertAlmostEqual(game.household.artisans, 4 * game.MANUMISSION_ARTISAN_UPLIFT)

    def test_freed_people_move_from_slaves_to_freedmen(self):
        game, _freed = self.freed()
        self.assertEqual((game.household.slaves, game.household.freedmen, game.household.manumitted_total), (0, 4, 4))

    def test_freeing_people_still_in_training_adds_no_capacity_now_and_raises_what_they_will_be_worth(self):
        game, _freed = self.freed(trained=False)
        self.assertEqual(game.household.artisans, 0.0)
        worth = game.WORKER_EQUIVALENT_UNTRAINED + game.MANUMISSION_ARTISAN_UPLIFT
        self.assertAlmostEqual(game.household.training[0][0], 4 * worth)

    def test_nobody_to_free_changes_nothing(self):
        game = Bondage()
        self.assertEqual(game.manumit(3), 0)
        self.assertEqual(game.household.artisans, 0.0)


class GrantsSurviveTheYearsResync(unittest.TestCase):
    def resynced(self, game):
        with mock.patch.object(labour_bondage.trade_data, "scholar_trade", return_value="scholar"):
            game._resync_pools()
        return game.household

    def test_a_grant_is_recorded_and_added_to_the_pools_at_once(self):
        game = Bondage()
        game._grant_staff(scholars=4)
        self.assertEqual(game.household.granted_staff, {"scholars": 4, "artisans": 0.0})
        self.assertEqual(game.household.scholars, 4)

    def test_the_yearly_resync_adds_the_grant_back_instead_of_discarding_it(self):
        game = Bondage()
        game._grant_staff(scholars=4)
        self.assertEqual(self.resynced(game).scholars, 4)

    def test_the_pools_are_the_people_on_the_books_plus_the_grant(self):
        game = Bondage(employees={"scholar": 2.0, "smith": 3.0})
        game._grant_staff(scholars=4, artisans=1)
        household = self.resynced(game)
        self.assertEqual((household.scholars, household.artisans), (6.0, 4.0))

    def test_people_bought_and_still_learning_are_not_counted_as_artisans(self):
        game = Bondage()
        game.household.slaves = 12
        game.household.training = [[12 * game.WORKER_EQUIVALENT_UNTRAINED, YEAR + 3.0]]
        self.assertAlmostEqual(self.resynced(game).artisans, 0.0)

    def test_people_bought_and_trained_count_at_the_slave_productivity(self):
        game = Bondage()
        game.household.slaves = 10
        self.assertAlmostEqual(self.resynced(game).artisans, 10 * game.TRAINED_SLAVE_ARTISAN_PRODUCTIVITY)


if __name__ == "__main__":
    unittest.main()
