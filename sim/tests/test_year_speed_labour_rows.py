"""Labour bids and offers as rows (stage 4): the bid table and the core's tranches cut from it, the plan table's labour rows, the cohorts'
offers written as columns, the settled offers the fills read, and the keep paid as postings each equal the objects they replaced, to the
last digit, on written-out inputs and random ones. No game."""

QUICK_TOPIC = True

import random
import types
import unittest

import numpy

from sim.book import Book
from sim.economy import bondage_keep, households_cohort
from sim.economy.bondage_rows import KeepRows
from sim.economy.households_cohort import Cohort
from sim.economy.labour_bid_sink import put_bids
from sim.economy.labour_fills import MarketRows, BuyRows, fills_of
from sim.economy.labour_offer_rows import LabourOfferRows
from sim.economy.labour_offers_table import build_labour_offers
from sim.economy.labour_offers_write import _area_numbers, write_cohort_offers
from sim.economy.labour_supply import HourSupply
from sim.economy.labour_sold_offers import SoldOffers, sold_hours_by_worker
from sim.economy.plan_table import BidColumns as PlanBidColumns, LabourColumns, PlanTable
from sim.economy.types import LabourBid, LabourOffer, Transfer
from sim.economy.year_ledger import YearLedger
from sim.labour.api import LabourBidTable, TrancheBids
from sim.labour.market import bid_book
from sim.labour.market.market_state import MarketState

TRADES = ("smith", "miller", "labourer")
AREAS = ("work@a", "work@b", "work@c")


def random_bids(rng, count):
    return [LabourBid("firm%d" % rng.randrange(7), rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(10, 9000)]),
                      rng.uniform(0.2, 3.0)) for _each in range(count)]


class BidTable(unittest.TestCase):
    def test_rows_keep_the_order_they_came_in_whatever_way_they_came(self):
        table = LabourBidTable()
        table.add("b", "smith", "work@a", 10.0, 1.0)
        table.add_named(["a", "b"], ["miller", "smith"], ["work@b", "work@a"], [20.0, 30.0], [2.0, 3.0])
        table.add_objects([LabourBid("c", "smith", "work@c", 40.0, 4.0)])
        table.add_rows(numpy.array([0]), numpy.array([0]), numpy.array([1]), numpy.array([50.0]), numpy.array([5.0]))
        self.assertEqual([(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in table],
                         [("b", "smith", "work@a", 10.0, 1.0), ("a", "miller", "work@b", 20.0, 2.0), ("b", "smith", "work@a", 30.0, 3.0),
                          ("c", "smith", "work@c", 40.0, 4.0), ("b", "smith", "work@b", 50.0, 5.0)])

    def test_hours_cut_in_the_table_stay_cut_and_later_rows_follow(self):
        table = LabourBidTable()
        table.add("a", "smith", "work@a", 10.0, 1.0)
        table.table().hours[0] = 4.0
        table.add("a", "smith", "work@a", 7.0, 1.0)
        self.assertEqual(table.table().hours.tolist(), [4.0, 7.0])
        self.assertEqual(int(table.table().row_count[0]), 2)

    def test_a_copy_is_cut_on_its_own(self):
        table = LabourBidTable()
        table.add("a", "smith", "work@a", 10.0, 1.0)
        found = table.copy()
        found.table().hours[0] = 1.0
        self.assertEqual((table.table().hours.tolist(), found.table().hours.tolist()), ([10.0], [1.0]))

    def test_nothing_makes_an_empty_table(self):
        self.assertEqual((len(LabourBidTable()), LabourBidTable().table().hours.tolist(), list(LabourBidTable())), (0, [], []))

    def test_a_list_gets_records_and_a_table_gets_rows_from_the_same_figures(self):
        figures = [("m", "smith", "work@a", 3.0, 1.5), ("m", "miller", "work@b", 4.0, 2.5)]
        found, table = [], LabourBidTable()
        put_bids(found, figures)
        put_bids(table, figures)
        self.assertEqual(found, [LabourBid(*each) for each in figures])
        self.assertEqual([(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in table], figures)


class TranchesFromRows(unittest.TestCase):
    def state(self, bids):
        state = MarketState()
        state.admit({bid.area for bid in bids if bid.hours > 0.0}, [trade for trade in TRADES])
        return state

    def test_random_bids_are_numbered_and_cut_as_the_records_were(self):
        rng = random.Random(2)
        for _round in range(60):
            bids = random_bids(rng, rng.randrange(0, 40))
            table = LabourBidTable()
            table.add_objects(bids)
            from_records, from_rows = self.state(bids), self.state(bids)
            records, rows = TrancheBids(bids, 4, 0.3), TrancheBids(table, 4, 0.3)
            self.assertEqual(len(rows), len(records))
            self.assertEqual((rows.trade_names(), rows.area_names()), (records.trade_names(), records.area_names()))
            found, wanted = bid_book.numbered(from_rows, rows), bid_book.numbered(from_records, records)
            for name in wanted._fields:
                self.assertEqual(getattr(found, name).tolist(), getattr(wanted, name).tolist(), name)
            self.assertEqual(from_rows.ids.employers.table.names, from_records.ids.employers.table.names)
            self.assertEqual(list(rows), list(records))
            self.assertEqual(bid_book.area_names(rows), bid_book.area_names(records))


class PlanTableLabour(unittest.TestCase):
    def test_the_labour_rows_become_the_bids_of_the_objects(self):
        labour = LabourColumns(numpy.array([0, 0, 2]), numpy.array([1, 0, 1]), numpy.array([0, 1, 1]), numpy.array([5.0, 6.0, 7.0]),
                               numpy.array([1.5, 2.5, 3.5]))
        bids = PlanBidColumns(numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64),
                              numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64), numpy.zeros((0, 6)))
        plans = PlanTable(("p0", "p1", "p2"), [1.0, 0.0, 1.0], [1.0, 0.0, 1.0], numpy.zeros(3), bids, labour, [], [], ["work@a", "work@b"], None,
                          ["smith", "miller"])
        table = LabourBidTable()
        plans.write_labour_bids(table)
        self.assertEqual([(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in table],
                         [(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage) for bid in plans.labour_bid_objects()])
        self.assertEqual([(bid.employer, bid.trade, bid.area) for bid in table],
                         [("p0", "miller", "work@a"), ("p0", "smith", "work@b"), ("p2", "miller", "work@b")])


def as_matrix(people_in_area):
    """A per-area `people_in_area(area)` dict as the block form `write_cohort_offers` takes: (people per area and trade, trade names)."""
    def people_in_areas(areas):
        found = [people_in_area(area) for area in areas]
        names = sorted({trade for each in found for trade in each})
        return numpy.array([[each.get(trade, 0.0) for trade in names] for each in found], dtype=float).reshape(len(areas), len(names)), names
    return people_in_areas


def plain_cohort_offers(cohorts, people_in_area, area_of, subsistence, hours_per_year, danger, levy, levied):
    """What `year_labour.labour_offers` did: each cohort's offers by `households_cohort.labour_offers`, cohorts by id."""
    working = {}
    for cohort in cohorts:
        working[cohort.tile] = working.get(cohort.tile, 0.0) + cohort.working_people
    offers = []
    for cohort in sorted(cohorts, key=lambda each: each.agent_id):
        tile_working = working.get(cohort.tile, 0.0)
        share = cohort.working_people / tile_working if tile_working > 0.0 else 0.0
        people = people_in_area("work@" + cohort.tile)
        hours_left = hours_per_year
        if cohort.tile in set(levied):
            hours_left = max(0.0, hours_left - max(0.0, levy))
        if hours_left <= 0.0:
            continue
        offers.extend(households_cohort.labour_offers(cohort, {trade: count * share for trade, count in people.items()},
                                                      types.SimpleNamespace(area_of=area_of), subsistence.get(cohort.tile, 0.0), hours_left, danger))
    return offers


class CohortOffers(unittest.TestCase):
    def test_random_cohorts_make_the_offers_the_objects_were(self):
        rng = random.Random(4)
        tiles = ("a", "b", "c")
        for _round in range(80):
            cohorts = [Cohort("household:%s:%d" % (tile, number), tile, number, rng.uniform(10, 900), rng.choice([0.0, rng.uniform(1, 400)]), 0.3)
                       for tile in tiles for number in range(rng.randrange(0, 4))]
            people = {"work@" + tile: {trade: rng.choice([0.0, rng.uniform(0.1, 300)]) for trade in rng.sample(TRADES, rng.randrange(0, 4))}
                      for tile in tiles}
            area_of = lambda trade, tile: "work@" + tile
            subsistence = {tile: rng.uniform(100, 900) for tile in tiles[:rng.randrange(0, 4)]}
            danger = {"smith": 0.01, "miller": 0.0}
            hours, levy, levied = 2000.0, rng.choice([0.0, 300.0, 5000.0]), rng.sample(tiles, rng.randrange(0, 3))
            rows = LabourOfferRows()
            write_cohort_offers(rows, cohorts, as_matrix(lambda area: people[area]), lambda tile: "work@" + tile, subsistence, hours, danger, levy, levied)
            self.assertEqual(list(rows.objects()), plain_cohort_offers(cohorts, lambda area: people[area], area_of, subsistence, hours, danger, levy,
                                                                       levied))

    def test_area_numbers_follow_the_sorted_trade_tile_pairs_for_new_areas(self):
        rows = LabourOfferRows()
        rows.areas.number("work@x")
        area_of_tile = {4: "work@d", 2: "work@b", 7: "work@x"}
        chosen_tile = numpy.array([4, 2, 7, 2])
        row_cohort = numpy.array([0, 1, 2, 3, 0, 1])
        trade = numpy.array([1, 1, 1, 1, 0, 0])
        found = _area_numbers(rows, area_of_tile, chosen_tile, row_cohort, trade)
        # tiles rank 4:0, 2:1, 7:2; the pairs sorted by (trade, rank) reach work@d first, then work@b
        self.assertEqual(rows.areas.names, ["work@x", "work@d", "work@b"])
        self.assertEqual(found.tolist(), [1, 2, 0, 2, 1, 2])

    def test_cohorts_taken_in_any_order_give_the_offers_by_id(self):
        cohorts = [Cohort("household:b:0", "b", 0, 100.0, 50.0, 0.5), Cohort("household:a:0", "a", 0, 100.0, 50.0, 0.5)]
        rows = LabourOfferRows()
        write_cohort_offers(rows, cohorts, as_matrix(lambda area: {"smith": 10.0, "labourer": 4.0}),
                            lambda tile: "work@" + tile, {}, 2000.0, {})
        self.assertEqual([(offer.worker, offer.trade, offer.hours) for offer in rows], [
            ("household:a:0", "labourer", 4.0 * 2000.0), ("household:a:0", "smith", 10.0 * 2000.0),
            ("household:b:0", "labourer", 4.0 * 2000.0), ("household:b:0", "smith", 10.0 * 2000.0)])


def random_offers(rng, count):
    return [LabourOffer("cohort%d" % rng.randrange(9), rng.choice(TRADES), rng.choice(AREAS), rng.choice([0.0, rng.uniform(100, 9000)]),
                        rng.uniform(0.1, 2.0)) for _each in range(count)]


class OffersOnRows(unittest.TestCase):
    def test_the_table_of_rows_is_the_table_of_the_records(self):
        rng = random.Random(6)
        for _round in range(40):
            offers = random_offers(rng, rng.randrange(0, 30))
            plan, work = {"cohort1": 40.0}, {"cohort2": 7.0, "cohort3": 3.0}
            rows = LabourOfferRows.of_objects(offers)
            found, ids, markets = build_labour_offers(rows, plan, work, {})
            wanted, wanted_ids, wanted_markets = build_labour_offers(offers, plan, work, {})
            for name in found._fields:
                self.assertEqual(getattr(found, name).tolist(), getattr(wanted, name).tolist(), name)
            self.assertEqual((ids.cohorts.names, ids.trades.names, ids.areas.names), (wanted_ids.cohorts.names, wanted_ids.trades.names,
                                                                                   wanted_ids.areas.names))
            self.assertEqual(markets.trade_of_market.tolist(), wanted_markets.trade_of_market.tolist())

    def test_names_shared_with_bids_do_not_add_trades_to_the_offers_numbering(self):
        bids = LabourBidTable()
        bids.add("firm", "zebra", "work@z", 5.0, 1.0)
        rows = LabourOfferRows(bids.trades, bids.areas)
        rows.add("c", "smith", "work@a", 100.0, 1.0)
        _table, ids, _markets = build_labour_offers(rows, {}, {}, {})
        self.assertEqual((ids.trades.names, ids.areas.names), (("smith",), ("work@a",)))

    def test_the_settled_offers_are_the_records_with_the_hours_sold_and_fill_the_same_markets(self):
        rng = random.Random(9)
        for _round in range(40):
            offers = random_offers(rng, rng.randrange(1, 30))
            records = HourSupply(offers, {"cohort1": 40.0}, {"cohort2": 7.0}, {})
            rows = HourSupply(LabourOfferRows.of_objects(offers), {"cohort1": 40.0}, {"cohort2": 7.0}, {})
            cleared = {(trade, area): rng.uniform(0.1, 2.0) for trade in TRADES for area in AREAS if rng.random() < 0.7}
            from_records, from_rows = records.settle(cleared), rows.settle(cleared)
            self.assertIsInstance(from_rows, SoldOffers)
            self.assertEqual(list(from_rows), list(from_records))
            self.assertEqual(rows.kept, records.kept)
            self.assertEqual(from_rows.hours_by_worker(), sold_hours_by_worker(list(from_records)))
            markets = sorted(cleared)
            hired = numpy.array([rng.uniform(0.0, 3000.0) for _market in markets])
            market_rows = MarketRows([trade for trade, _area in markets], [area for _trade, area in markets], numpy.ones(len(markets)), hired,
                                     numpy.zeros(len(markets)), numpy.zeros(len(markets)))
            buys = BuyRows(numpy.arange(len(markets) + 1, dtype=numpy.int64), numpy.zeros(len(markets), dtype=numpy.int64), hired)
            found, wanted = fills_of(market_rows, buys, ["firm"], from_rows), fills_of(market_rows, buys, ["firm"], list(from_records))
            self.assertEqual(found.names, wanted.names)
            for name in ("buy_start", "buy_ref", "buy_hours", "sell_start", "sell_ref", "sell_hours"):
                self.assertEqual(getattr(found, name).tolist(), getattr(wanted, name).tolist(), name)

    def test_the_wage_each_market_faces_is_the_last_offers_reservation_unless_a_wage_is_recorded(self):
        rows = LabourOfferRows.of_objects([LabourOffer("a", "smith", "work@a", 1.0, 0.5), LabourOffer("b", "smith", "work@a", 1.0, 0.7),
                                           LabourOffer("a", "miller", "work@b", 1.0, 0.9)])
        faced = rows.faced_wages(lambda trade, area: 2.0 if trade == "miller" else None, lambda recorded, reservation: reservation if recorded is None else recorded)
        self.assertEqual(faced, {("smith", "work@a"): 0.7, ("miller", "work@b"): 2.0})


class KeepPostings(unittest.TestCase):
    def books(self):
        found = []
        for _each in range(2):
            book = Book()
            book.transfer(Transfer("edge:legacy", "works0", "coin", 50.0, "opening"))
            book.transfer(Transfer("edge:legacy", "works1", "coin", 20.0, "opening"))
            found.append(book)
        return found

    def test_the_rows_move_the_money_the_transfers_did(self):
        posted, objects = self.books()
        keep = KeepRows(["works0", "works1", "works0"], ["household:a", "household:b", "household:b"], [10.0, 5.5, 2.25])
        ledger = YearLedger()
        bondage_keep.post_keep(posted, ledger, keep, "coin")
        objects.transfer_many([Transfer(employer, cohort, "coin", amount, "keep of bonded") for employer, cohort, amount in keep])
        for agent in ("works0", "works1", "household:a", "household:b"):
            self.assertEqual(posted.balance(agent, "coin"), objects.balance(agent, "coin"), agent)
        self.assertEqual(ledger.money_out["works0"], 12.25)
        self.assertEqual(ledger.money_out["works1"], 5.5)

    def test_a_refused_batch_raises_the_books_own_error_and_posts_nothing(self):
        book = self.books()[0]
        keep = KeepRows(["works1"], ["household:a"], [500.0])
        with self.assertRaises(Exception) as raised:
            bondage_keep.post_keep(book, YearLedger(), keep, "coin")
        self.assertIn("works1", str(raised.exception))
        self.assertEqual(book.balance("works1", "coin"), 20.0)

    def test_nothing_to_pay_posts_nothing(self):
        book = self.books()[0]
        bondage_keep.post_keep(book, YearLedger(), KeepRows([], [], []), "coin")
        self.assertEqual(book.balance("works0", "coin"), 50.0)


if __name__ == "__main__":
    unittest.main()
